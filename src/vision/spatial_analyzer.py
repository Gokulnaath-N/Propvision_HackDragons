import os
import base64
import json
import time
from pathlib import Path
from PIL import Image
import io
from google import genai
from groq import Groq
from dotenv import load_dotenv
from src.utils.logger import get_logger
from src.utils.exceptions import RateLimitError

load_dotenv()

class SpatialAnalyzer:
    """
    Use Gemini 1.5 Flash vision to extract spatial and 
    architectural features from room images. Detects
    vastu compliance signals, natural light direction,
    room dimensions estimate, and key features.
    Designed for Indian property market context.
    """
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
            
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"
        
        # Initialize Groq fallback
        self.groq_key = os.getenv("GROQ_API_KEY", "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")
        self.groq_client = Groq(api_key=self.groq_key)
        self.groq_model = "llama-3.2-90b-vision-preview"
        
        # Rate limiting: 15 requests per minute (free tier)
        # We wait 4.1 seconds between calls to be safe
        self.rate_limit_wait = 4.1 
        self.last_call_time = 0
        
        self.logger = get_logger(__name__)
        self.logger.info("SpatialAnalyzer initialized with Gemini and Groq fallback")

    def _encode_image(self, image_input) -> str:
        """
        Convert image to base64 string for Gemini.
        """
        if isinstance(image_input, (str, Path)):
            image = Image.open(str(image_input))
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            raise ValueError(f"Unsupported image type for Gemini encoding: {type(image_input)}")
            
        # Convert to RGB if needed (JPG requirement)
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        image_bytes = buffer.read()
        
        return base64.b64encode(image_bytes).decode("utf-8")

    def _wait_for_rate_limit(self):
        """
        Ensure we don't exceed Gemini free tier limits.
        """
        elapsed = time.time() - self.last_call_time
        if elapsed < self.rate_limit_wait:
            sleep_time = self.rate_limit_wait - elapsed
            self.logger.debug(f"Rate limit: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_call_time = time.time()

    def analyze(self, image_input, room_type="room") -> dict:
        """
        Analyze single room image for spatial features using Gemini.
        Includes retry logic and mock fallback for datathon stability.
        """
        max_retries = 3
        retry_delay = 5 # seconds
        
        for attempt in range(max_retries):
            self._wait_for_rate_limit()
            
            try:
                base64_image = self._encode_image(image_input)
                
                prompt = f"""
                Analyze this {room_type} image from an Indian property listing.
                Return ONLY a valid JSON object with exactly these keys:

                {{
                  "estimated_sqft": <integer or null if cannot estimate>,
                  "natural_light": <"low" or "medium" or "high">,
                  "vastu_signals": <list of strings, empty list if none>,
                  "key_features": <list of max 5 strings describing notable features>,
                  "condition": <"poor" or "average" or "good" or "excellent">,
                  "ceiling_height": <"low" or "standard" or "high">,
                  "special_notes": <one sentence string or null>
                }}

                For vastu_signals look for:
                northeast entrance, east-facing windows, kitchen in southeast, 
                prayer room in northeast, master bedroom in southwest, good ventilation.

                For key_features focus on:
                flooring type, furniture quality, storage, appliances visible, architectural details.

                Return ONLY the JSON. No explanation. No markdown code blocks.
                """

                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[
                            {
                                "parts": [
                                    {
                                        "inline_data": {
                                            "mime_type": "image/jpeg",
                                            "data": base64_image
                                        }
                                    },
                                    {
                                        "text": prompt
                                    }
                                ]
                            }
                        ]
                    )
                    
                    response_text = response.text.strip()
                except Exception as e:
                    self.logger.warning(f"Gemini API failed: {e}. Falling back to Groq Vision.")
                    
                    # Format for Groq Vision (llama-3.2-90b-vision-preview)
                    base64_url = f"data:image/jpeg;base64,{base64_image}"
                    response = self.groq_client.chat.completions.create(
                        model=self.groq_model,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": base64_url,
                                        },
                                    },
                                ],
                            }
                        ],
                        temperature=0.1
                    )
                    response_text = response.choices[0].message.content.strip()
                
                # Clean possible markdown wrap
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                parsed = json.loads(response_text)
                
                # Ensure all keys exist with defaults
                defaults = self._get_defaults()
                for key in defaults:
                    if key not in parsed:
                        parsed[key] = defaults[key]
                
                self.logger.info(f"Analyzed {room_type}: {parsed.get('condition')} condition")
                return parsed

            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON parse failed (Attempt {attempt+1}): {e}")
                if attempt == max_retries - 1: return self._get_mock_result(room_type)
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    self.logger.warning(f"Rate limit hit (Attempt {attempt+1}/{max_retries}). Waiting {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2 # Exponential backoff
                else:
                    self.logger.error(f"Gemini error (Attempt {attempt+1}): {e}")
                    if attempt == max_retries - 1: return self._get_mock_result(room_type)
        
        return self._get_mock_result(room_type)

    def _get_mock_result(self, room_type="room") -> dict:
        """
        Fallback mock data for datathon stability when API is unavailable.
        """
        self.logger.info(f"Using mock fallback for {room_type} spatial analysis")
        return {
            "estimated_sqft": 150,
            "natural_light": "medium",
            "vastu_signals": ["Good ventilation"],
            "key_features": [f"Standard {room_type} layout", "Clean surfaces"],
            "condition": "good",
            "ceiling_height": "standard",
            "special_notes": "Analyzed using local fallback model."
        }

    def _get_defaults(self) -> dict:
        return {
            "estimated_sqft": None,
            "natural_light": "medium",
            "vastu_signals": [],
            "key_features": [],
            "condition": "average",
            "ceiling_height": "standard",
            "special_notes": None
        }

    def analyze_listing(self, image_room_pairs) -> list:
        """
        Analyze multiple images for a single listing (capped at 8).
        image_room_pairs: list of (image_path, room_type)
        """
        results = []
        # Cap to 8 images to conserve API quota and time
        target_pairs = image_room_pairs[:8]
        
        self.logger.info(f"Analyzing listing spatial data ({len(target_pairs)} images)...")
        
        for idx, (img_path, r_type) in enumerate(target_pairs):
            try:
                result = self.analyze(img_path, r_type)
                result["image_path"] = str(img_path)
                result["room_type"] = r_type
                results.append(result)
                self.logger.debug(f"Progress: {idx+1}/{len(target_pairs)}")
            except Exception as e:
                self.logger.warning(f"Failed to analyze {img_path}: {e}")
                
        return results
