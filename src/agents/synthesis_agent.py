import os
import json
import time
from google import genai
from groq import Groq
from dotenv import load_dotenv
from src.agents.state import ListingState, QueryState
from src.utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


class SynthesisAgent:
    """
    Uses Gemini 1.5 Flash to synthesize all ML analysis results into
    human-readable listing summaries and personalized match explanations.
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
        
        self.rate_limit_wait = 4.1
        self.last_call_time = 0
        logger.info("SynthesisAgent initialized with Groq fallback")

    def _wait(self):
        """Wait to respect the API rate limit."""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.rate_limit_wait:
            time.sleep(self.rate_limit_wait - elapsed)
        self.last_call_time = time.time()

    def synthesize_listing(self, state: ListingState) -> ListingState:
        """
        LangGraph node — generate listing intelligence based on all aggregated ML data.
        """
        state["processing_status"] = "synthesizing"

        # Collect all data
        room_types = [c.get("room_type") for c in state.get("room_classifications", []) if c.get("room_type")]
        unique_rooms = list(set(room_types))

        grades = [q.get("grade") for q in state.get("quality_scores", []) if q.get("grade")]
        
        # Calculate overall grade based on simple scoring
        grade_scores = {"A+": 6, "A": 5, "B+": 4, "B": 3, "C": 2, "D": 1}
        reverse_scores = {6: "A+", 5: "A", 4: "B+", 3: "B", 2: "C", 1: "D"}
        
        overall_grade = "N/A"
        if grades:
            avg_score = round(sum(grade_scores.get(g, 1) for g in grades) / len(grades))
            avg_score = max(1, min(6, avg_score))
            overall_grade = reverse_scores.get(avg_score, "C")
            
        state["overall_grade"] = overall_grade

        spatial_data = state.get("spatial_analyses", [])
        vastu_signals = []
        key_features = []
        
        for analysis in spatial_data:
            vastu_signals.extend(analysis.get("vastu_signals", []))
            key_features.extend(analysis.get("key_features", []))
            
        vastu_signals = list(set(vastu_signals))
        key_features = list(set(key_features))

        metadata = state.get("metadata", {})

        self._wait()

        # Build prompt
        prompt = f"""Generate a property listing summary for an Indian property.
        
Property Details:
- Location: {metadata.get('city', 'Not specified')}
- Price: {metadata.get('price', 'Not specified')} rupees
- BHK: {metadata.get('bhk', 'Not specified')}
- Rooms photographed: {unique_rooms}
- Image quality grade: {overall_grade}
- Vastu signals found: {vastu_signals}
- Key features detected: {key_features[:10]}

Return ONLY JSON with these keys:
{{
  "summary": "<2-3 sentence property description highlighting best features for Indian buyers>",
  "highlights": ["<list of 4-5 key selling points>"],
  "vastu_compliance": "<brief vastu assessment>",
  "action_items": ["<list of improvements broker should make to improve listing quality>"],
  "buyer_appeal": "<one sentence on who this property is ideal for>"
}}

Return ONLY JSON, no markdown, no explanation.
"""

        try:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                text = response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API failed in SynthesisAgent: {e}. Falling back to Groq Llama 3.")
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                text = response.choices[0].message.content.strip()

            text = text.replace("```json", "").replace("```", "")
            result = json.loads(text)

            state["listing_summary"] = result.get("summary", "")
            state["action_items"] = result.get("action_items", [])
            state["processing_status"] = "complete"

            logger.info(f"Synthesis complete for {state.get('listing_id', 'unknown')}")

        except Exception as e:
            logger.error(f"Synthesis failed (both APIs): {e}")
            state["listing_summary"] = f"Property in {metadata.get('city', 'India')}"
            state["action_items"] = []
            state["processing_status"] = "complete"

        return state

    def generate_match_explanation(self, listing_payload: dict, query_intent: dict) -> str:
        """
        Explain why a listing matches user query. Used by search pipeline per result.
        """
        self._wait()

        prompt = f"""Explain in ONE sentence why this property matches what the buyer is looking for.

Buyer wants: {json.dumps(query_intent)}
Property: {json.dumps(listing_payload)}

Write from property perspective to the buyer.
Be specific about matching features.
Maximum 30 words.
Return ONLY the sentence, no JSON, no quotes.
"""

        try:
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API failed for match explanation: {e}. Falling back to Groq Llama 3.")
                response = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
        except:
            city = listing_payload.get('city', '')
            return f"Property in {city} matching your requirements" if city else "Property matching your requirements"

    def generate_batch_explanations(self, results: list, query_intent: dict) -> dict:
        """
        Generate explanations for all search results.
        Returns dict: listing_id -> explanation string.
        """
        explanations = {}
        # Only generate for the top 10 to limit API calls and latency
        for result in results[:10]:
            try:
                explanation = self.generate_match_explanation(result, query_intent)
                # Fallback if listing_id is missing
                listing_id = result.get("listing_id")
                if listing_id:
                    explanations[listing_id] = explanation
            except Exception as e:
                logger.error(f"Batch explanation failed for a result: {e}")
                
        return explanations
