import os
import json
import time
from google import genai
from groq import Groq
from dotenv import load_dotenv
from src.agents.state import QueryState
from src.utils.logger import get_logger
from src.utils.exceptions import RateLimitError

load_dotenv()

logger = get_logger(__name__)


class QueryAgent:
    """
    Parses natural language property search queries using Gemini 1.5 Flash.
    Extracts structured intent for both database filtering and CLIP semantic search.
    Handles Indian property context: crore/lakh, vastu, pooja room, Indian city names.
    """

    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        self.model = "gemini-1.5-flash"
        
        # Initialize Groq fallback
        self.groq_key = os.getenv("GROQ_API_KEY", "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")
        self.groq_client = Groq(api_key=self.groq_key)
        self.groq_model = "llama-3.3-70b-versatile"
        
        self.last_call_time = 0
        self.rate_limit_wait = 4.1
        logger.info("QueryAgent initialized with Groq fallback")

    def parse_query(self, state: QueryState) -> QueryState:
        """
        Main LangGraph node function.
        Parses raw_query and updates state with parsed_intent.
        """
        query = state["raw_query"]
        history = state.get("conversation_history", [])

        # Wait for rate limit
        elapsed = time.time() - self.last_call_time
        if elapsed < self.rate_limit_wait:
            time.sleep(self.rate_limit_wait - elapsed)
        self.last_call_time = time.time()

        # Build context from conversation history
        if history:
            previous_queries = [
                h["content"] for h in history if h.get("role") == "user"
            ]
            recent_queries = previous_queries[-2:]
            context = "Previous searches: " + " | ".join(recent_queries)
        else:
            context = ""

        # Build prompt
        prompt = f"""You are a property search assistant for Indian real estate.
{context}

Parse this search query: "{query}"

Return ONLY a valid JSON with these exact keys:
{{
  "location": "<city or area name or null>",
  "bhk": <integer 1-5 or null>,
  "price_min": <integer in rupees or null>,
  "price_max": <integer in rupees or null>,
  "vastu": <true or false or null>,
  "property_type": "<flat/house/villa or null>",
  "room_features": {{
    "<room_type>": "<description of what user wants>"
  }},
  "amenities": ["<list of amenities>"],
  "clip_search_query": "<single sentence describing visual features of ideal property for image search>"
}}

IMPORTANT RULES:
- Convert crore to rupees: 1 crore = 10000000
- Convert lakh to rupees: 1 lakh = 100000
- clip_search_query must be visual and descriptive
- Example: "spacious modern apartment interior with natural light wooden flooring clean rooms"
- Return ONLY JSON, no explanation, no markdown
"""

        try:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                text = response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API failed in QueryAgent: {e}. Falling back to Groq Llama 3.")
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                text = response.choices[0].message.content.strip()

            text = text.replace("```json", "").replace("```", "")
            parsed = json.loads(text)

            # Validate all required keys exist; set missing ones to safe defaults
            required_keys = [
                "location", "bhk", "price_min", "price_max",
                "vastu", "clip_search_query"
            ]
            for key in required_keys:
                if key not in parsed:
                    parsed[key] = None

            if "property_type" not in parsed:
                parsed["property_type"] = None
            if "room_features" not in parsed:
                parsed["room_features"] = {}
            if "amenities" not in parsed:
                parsed["amenities"] = []

            state["parsed_intent"] = parsed

            # Build database filters from parsed intent
            filters = {}
            if parsed.get("location"):
                filters["city"] = parsed["location"]
            if parsed.get("bhk"):
                filters["bhk"] = parsed["bhk"]
            if parsed.get("price_max"):
                filters["price_max"] = parsed["price_max"]
            if parsed.get("price_min"):
                filters["price_min"] = parsed["price_min"]
            if parsed.get("vastu") is not None:
                filters["vastu"] = parsed["vastu"]
            state["filters"] = filters

            # Add to conversation history
            state["conversation_history"].append({
                "role": "user",
                "content": query,
                "parsed": parsed
            })

            logger.info(f"Query parsed: {json.dumps(parsed, indent=2)}")
            return state

        except json.JSONDecodeError:
            logger.warning("JSON parse failed (both APIs), using defaults")
            state["parsed_intent"] = self._default_intent(query)
            state["filters"] = {}
            return state

        except Exception as e:
            logger.error(f"Query parsing failed: {e}")
            state["parsed_intent"] = self._default_intent(query)
            state["filters"] = {}
            return state

    def _default_intent(self, query: str) -> dict:
        """
        Returns a safe default intent when parsing fails.
        Uses the raw query as a fallback for CLIP semantic search.
        """
        return {
            "location": None,
            "bhk": None,
            "price_min": None,
            "price_max": None,
            "vastu": None,
            "property_type": None,
            "room_features": {},
            "amenities": [],
            "clip_search_query": query,  # Raw query as CLIP fallback
        }
