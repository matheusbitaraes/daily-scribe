"""
Summarization service for Daily Scribe application.

This module handles summarizing article text using the Gemini API and OpenAI API.
"""

import logging
import re
import time
import datetime
import os
import google.generativeai as genai
import openai
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class NewsMetadata(BaseModel):
    summary: str = Field(description="Summarize the following text in approximately 40 to 100 words and DO IT ALWAYS IN THE ORIGINAL LANGUAGE OF THE ARTICLE (LIMITED TO ENGLISH OR BRAZILIAN PORTUGUESE).")
    summary_pt: str = Field(description="Summarize the following text in approximately 40 to 100 words and DO IT ALWAYS IN PORTUGUESE, no matter the original language of the article. Make the summary as a news article summary. Don't repeat information that is present in the title. Make it concise and interesting")
    title_pt: str = Field(description="Translate the title of the article to Portuguese. If the original title is already in Portuguese, repeat it exactly as is. Attention: don't make the title will all words in capital leters. Example, instead of 'Dólar Atinge Nível Mais Alto Devido à China', do 'Dólar atinge nível mais alto devido à China")
    sentiment: str = Field(description="The overall sentiment of the article (Positive, Negative, Neutral).")
    keywords: List[str] = Field(description="A list of key people, organizations, or locations mentioned.")
    category: str = Field(description="The main category of the news. Select one of those options: 'Politics', 'Technology', 'Science and Health', 'Business', 'Entertainment', 'Sports'. Use the category 'Other' if none of the options fit.")
    region: str = Field(description="The primary geographical place the news is about (e.g., Brazil, USA, Europe, Asia).")
    urgency_score: int = Field(description="Rate the urgency of this news on a scale of 0-100. 0-20=Evergreen (timeless content), 21-40=Long-Term (relevant for weeks/months), 41-60=Topical (recent events, follow-up), 61-80=Time-Sensitive (urgent, needs attention within days), 81-100=Breaking News (happening now or just occurred).")
    impact_score: int = Field(description="Rate the impact of this news on a scale of 0-100. 0-20=Minor Update (very low impact, small number of people), 21-40=Niche Impact (significant to specific community), 41-60=Moderate Impact (affects large community), 61-80=Significant Impact (major consequences for region/country/industry), 81-100=Major Development (landmark event with profound consequences).")
    subject_pt: str = Field(description="Create a very short 2-4 word phrase in Portuguese that can be used as part of an email subject line to represent this news headline. Make a cohesive very small phrase that captures the essence of the news. You can use prepositions, they don't count. So, intead of 'Conflito Gaza', you should use 'Conflito em Gaza'")

class Summarizer:
    """Handles summarizing text using the Gemini API and OpenAI API."""

    def __init__(self):
        """
        Initialize the summarizer.

        Args:
            config: The Gemini API configuration.
            openai_api_key: OpenAI API key (optional, will try to get from environment if not provided).
        """
        self.logger = logging.getLogger(__name__)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self._initialize_gemini()
        
        # Initialize OpenAI client
        self.openai_client = None
        self._initialize_openai()
        
        # Store quota exceeded status for each model in a dict
        self._quota_exceeded = {
            # Gemini models
            'gemini-3-flash-preview': False,
            'gemini-2.5-flash': False,
            'gemini-2.5-flash-lite': False,
            'gemini-2.0-flash': False,
            'gemini-2.0-flash-lite': False,
            'gemini-2.0-flash-001': False,
            'gemini-3-pro-preview': False,
            'gemini-2.5-pro': False, 
            # OpenAI models
            'gpt-5-nano': False,
            'gpt-4.1-nano': False,
            'gpt-4o-mini': False,
        }
        # List of model names in order of preference (mix of Gemini and OpenAI)
        self._model_order = [
            'gemini-3-flash-preview',
            'gemini-2.0-flash-lite',
            'gemini-2.5-flash-lite',
            'gemini-2.0-flash',
            'gemini-2.0-flash-001',
            'gemini-2.5-flash',
            'gemini-2.5-pro',
            'gemini-3-pro-preview',
            'gpt-5-nano',
            'gpt-4.1-nano',
            'gpt-4o-mini',
        ]
        # Track per-minute rate limit for each model
        self._rate_limited_until = {model: None for model in self._model_order}

    def _initialize_gemini(self):
        """
        Initialize the Gemini client.
        """
        try:
            self.logger.info("Initializing Gemini client.")
            genai.configure(api_key=self.gemini_api_key)
            self.logger.info("Gemini client initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def _initialize_openai(self):
        """
        Initialize the OpenAI client.
        """
        try:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            self.logger.info("OpenAI client initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            # Mark all OpenAI models as quota exceeded
            for model in self._model_order:
                if model.startswith('gpt-'):
                    self._quota_exceeded[model] = True

    def summarize(self, text: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Summarize the given text and extract metadata.
        """
        
        # Normal summarization flow
        return self._generate_full_metadata(text, max_retries)
    
    def _generate_full_metadata(self, text: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Generate full metadata including summary.
        """
        return self._generate_with_schema(text, NewsMetadata, max_retries, "Extract the requested metadata from the following news content")

    def _generate_with_schema(self, text: str, schema_class, max_retries: int, prompt_prefix: str) -> Dict[str, Any]:
        """
        Generate content using the specified schema with both Gemini and OpenAI models.
        """
        while True: # start all models iteration
            any_model_usable = False
            now = datetime.datetime.now()
            soonest_ready = None
            for model_name in self._model_order:
                until = self._rate_limited_until.get(model_name)
                if self._quota_exceeded.get(model_name):
                    continue
                if until and now < until:
                    if soonest_ready is None or until < soonest_ready:
                        soonest_ready = until
                    continue
                any_model_usable = True
                
                # Try the current model
                self.logger.info(f"Trying summarization with model: {model_name}")
                if model_name.startswith('gemini-'):
                    result = self._try_gemini_model(model_name, text, schema_class, prompt_prefix, max_retries)
                elif model_name.startswith('gpt-'):
                    result = self._try_openai_model(model_name, text, schema_class, prompt_prefix, max_retries)
                else:
                    continue
                
                if result is not None:
                    self.logger.info(f"Model {model_name} succeeded generating metadata.")
                    return result
                    
            if any_model_usable:
                # We tried all usable models, none succeeded, so exit
                break
            if soonest_ready:
                sleep_seconds = max(1, int((soonest_ready - datetime.datetime.now()).total_seconds()))
                self.logger.info(f"All models are rate-limited. Waiting {sleep_seconds} seconds for next available model.")
                time.sleep(sleep_seconds)
            else:
                break
        self.logger.error("Failed to generate metadata after trying all available models and retries.")
        return {}

    def _try_gemini_model(self, model_name: str, text: str, schema_class, prompt_prefix: str, max_retries: int) -> Dict[str, Any]:
        """
        Try to generate content using a Gemini model.
        """
        model = genai.GenerativeModel(model_name)
        prompt = f"{prompt_prefix}: {text}"
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=schema_class,
                    )
                )
                try:
                    part = response.candidates[0].content.parts[0]
                    if hasattr(part, 'text'):
                        import json
                        return json.loads(part.text)
                    if isinstance(part, dict):
                        return part
                except Exception as parse_exc:
                    self.logger.error(f"Failed to parse Gemini response as JSON: {parse_exc}")
                    return {}
            except Exception as e:
                error_message = str(e)
                self.logger.warning(f"[{model_name}] Attempt {attempt + 1} failed: {error_message}")
                if "GenerateRequestsPerDayPerProjectPerModel" in error_message:
                    self.logger.warning(f"Gemini API daily quota exceeded for {model_name}. Will not use this model anymore today.")
                    self._quota_exceeded[model_name] = True
                    break
                if "GenerateRequestsPerMinutePerProjectPerModel" in error_message:
                    wait_time = self._extract_wait_time(error_message) or 60
                    until = datetime.datetime.now() + datetime.timedelta(seconds=wait_time)
                    self._rate_limited_until[model_name] = until
                    self.logger.info(f"Model {model_name} is rate-limited until {until:%Y-%m-%d %H:%M:%S}.")
                    break
                else:
                    self.logger.error(f"An unexpected error occurred with {model_name}: {error_message}")
                    break
        return None

    def _try_openai_model(self, model_name: str, text: str, schema_class, prompt_prefix: str, max_retries: int) -> Dict[str, Any]:
        """
        Try to generate content using an OpenAI model.
        """
        if not self.openai_client:
            self.logger.warning(f"OpenAI client not available, skipping {model_name}")
            self._quota_exceeded[model_name] = True
            return None
            
        # Build JSON Schema from the Pydantic model for structured outputs
        schema_name = getattr(schema_class, "__name__", "ResponseSchema")
        try:
            schema_dict = schema_class.model_json_schema()
        except Exception:
            # Pydantic v1 fallback (not expected here, but safe)
            schema_dict = schema_class.schema() if hasattr(schema_class, "schema") else {}

        # Enforce additionalProperties: false recursively to satisfy OpenAI structured outputs
        try:
            import copy
            schema_for_openai = copy.deepcopy(schema_dict)
            self._enforce_no_additional_properties(schema_for_openai)
        except Exception as _:
            schema_for_openai = schema_dict
        
        messages = [
            {"role": "system", "content": f"{prompt_prefix}. Follow the JSON schema exactly and return only JSON, no prose."},
            {"role": "user", "content": text}
        ]

        def _get_openai_params_for_model(name: str, max_tokens_value: int = 1000) -> Dict[str, Any]:
            """
            Return the correct parameters dict for OpenAI API calls based on the model.
            Newer OpenAI gpt-5* models require:
            - max_completion_tokens instead of max_tokens
            - temperature parameter omitted (uses default value of 1)
            """
            params = {}
            if name.startswith("gpt-5"):
                params["max_completion_tokens"] = max_tokens_value
            else:
                params["max_tokens"] = max_tokens_value
                params["temperature"] = 0.1
            return params
        
        for attempt in range(max_retries):
            try:
                # First try OpenAI structured outputs with JSON Schema (strict)
                response = self.openai_client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name,
                            "schema": schema_for_openai,
                            "strict": True
                        }
                    },
                    **_get_openai_params_for_model(model_name, 1000),
                )
                
                content = response.choices[0].message.content
                if content:
                    try:
                        import json
                        result = json.loads(content)
                        # Validate against schema
                        validated = schema_class(**result)
                        return validated.model_dump()
                    except Exception as parse_exc:
                        self.logger.error(f"Failed to parse OpenAI response as JSON or validate schema: {parse_exc}")
                        continue
                        
            except Exception as e:
                error_message = str(e)
                self.logger.warning(f"[{model_name}] Attempt {attempt + 1} failed: {error_message}")
                # Fallback: model may not support json_schema response_format; try JSON mode with explicit schema instructions
                if "response_format" in error_message.lower() or "json_schema" in error_message.lower():
                    try:
                        fallback_messages = [
                            {
                                "role": "system",
                                "content": (
                                    f"{prompt_prefix}. You MUST respond with a JSON object that conforms to this JSON Schema. "
                                    f"Do not include any extra fields. Do not include any text outside JSON. "
                                    f"Schema: {schema_dict}"
                                )
                            },
                            {"role": "user", "content": text}
                        ]
                        response = self.openai_client.chat.completions.create(
                            model=model_name,
                            messages=fallback_messages,
                            response_format={"type": "json_object"},
                            **_get_openai_params_for_model(model_name, 1000),
                        )
                        content = response.choices[0].message.content
                        if content:
                            import json
                            result = json.loads(content)
                            validated = schema_class(**result)
                            return validated.model_dump()
                    except Exception as fallback_exc:
                        self.logger.warning(f"Fallback JSON mode also failed: {fallback_exc}")
                        # continue to rate limit/other error handling below
                if "rate_limit_exceeded" in error_message.lower() or "quota" in error_message.lower():
                    if "daily" in error_message.lower():
                        self.logger.error(f"OpenAI API daily quota exceeded for {model_name}. Will not use this model anymore today.")
                        self._quota_exceeded[model_name] = True
                        break
                    else:
                        # Rate limit, extract wait time and set rate limit
                        wait_time = self._extract_openai_wait_time(error_message) or 60
                        until = datetime.datetime.now() + datetime.timedelta(seconds=wait_time)
                        self._rate_limited_until[model_name] = until
                        self.logger.info(f"Model {model_name} is rate-limited until {until:%Y-%m-%d %H:%M:%S}.")
                        break
                else:
                    self.logger.error(f"An unexpected error occurred with {model_name}: {error_message}")
                    break
        return None

    def _extract_wait_time(self, error_message: str) -> int:
        """
        Extract the wait time from the Gemini error message.

        Args:
            error_message: The error message from the API.

        Returns:
            The wait time in seconds, or None if not found.
        """
        # Try to extract retry_delay { seconds: N } (with or without whitespace)
        match = re.search(r"retry_delay\s*\{[^}]*seconds:\s*(\d+)", error_message)
        if match:
            return int(match.group(1))
        # Try to extract retry after N
        match = re.search(r"retry after (\d+)", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Try to extract wait N seconds
        match = re.search(r"wait (\d+) seconds", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _extract_openai_wait_time(self, error_message: str) -> int:
        """
        Extract the wait time from the OpenAI error message.

        Args:
            error_message: The error message from the API.

        Returns:
            The wait time in seconds, or None if not found.
        """
        # Try to extract "retry after N seconds"
        match = re.search(r"retry after (\d+) seconds?", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Try to extract "Please try again in N seconds"
        match = re.search(r"try again in (\d+) seconds?", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Default wait time for OpenAI rate limits
        return 60

    def _enforce_no_additional_properties(self, schema: Dict[str, Any]):
        """
        Recursively enforce additionalProperties: false on JSON schema objects for OpenAI structured outputs.
        This helps avoid 400 errors requiring additionalProperties=false.
        """
        if not isinstance(schema, dict):
            return
        schema_type = schema.get("type")
        if schema_type == "object":
            # Ensure properties exists
            props = schema.get("properties", {})
            schema["properties"] = props
            # Disallow extra properties
            schema["additionalProperties"] = False
            # Recurse into nested object properties
            for prop_schema in props.values():
                self._enforce_no_additional_properties(prop_schema)
            # Handle patternProperties if present
            if "patternProperties" in schema and isinstance(schema["patternProperties"], dict):
                for pat_schema in schema["patternProperties"].values():
                    self._enforce_no_additional_properties(pat_schema)
        elif schema_type == "array":
            items = schema.get("items")
            if items:
                self._enforce_no_additional_properties(items)
        # Handle oneOf/anyOf/allOf branches
        for key in ("oneOf", "anyOf", "allOf"):
            if key in schema and isinstance(schema[key], list):
                for subschema in schema[key]:
                    self._enforce_no_additional_properties(subschema)