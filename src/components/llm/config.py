"""
Model configuration for the LLM abstraction layer.

Defines the fallback chain: free-tier models first, paid OpenAI models last.
"""

import os
from typing import List, Tuple


def get_model_config() -> Tuple[str, List[str]]:
    """
    Get the primary model and fallback list based on environment configuration.

    Order: Tier 1 (Gemini free) -> Tier 2 (Groq, DeepSeek, OpenRouter free) ->
    Tier 3 (Ollama optional) -> Tier 4 (OpenAI paid, last resort).

    Returns:
        Tuple of (primary_model, fallbacks_list). Fallbacks exclude the primary.
    """
    override = os.getenv("LLM_MODEL_OVERRIDE")
    if override:
        return override, []

    primary = None
    fallbacks: List[str] = []

    # Tier 1: OpenRouter (free)
    if os.getenv("OPENROUTER_API_KEY"):
        # go here to update the list: https://openrouter.ai/models?fmt=cards&input_modalities=text&max_price=0&order=top-weekly
        openrouter_models = [
            "openrouter/meta-llama/llama-3.3-70b-instruct:free"
            "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
            "openrouter/nvidia/nemotron-nano-9b-v2:free",
            "openrouter/stepfun/step-3.5-flash:free",
            "openrouter/z-ai/glm-4.5-air:free",
            "openrouter/deepseek/deepseek-r1-0528:free",
            "openrouter/nvidia/nemotron-3-nano-30b-a3b:free",
            "openrouter/qwen/qwen3-235b-a22b-thinking-2507",
            "openrouter/openai/gpt-oss-120b:free",
            "openrouter/arcee-ai/trinity-mini:free",
            "openrouter/qwen/qwen3-vl-235b-a22b-thinking",
            #  "openrouter/arcee-ai/trinity-large-preview:free", # this model didn't work well
        ]
            
        if primary is None:
            primary = openrouter_models[0]
            fallbacks.append(openrouter_models[1:])
        else:
            fallbacks.append(openrouter_models)

    #Tier 1: Gemini models (free)
    if os.getenv("GEMINI_API_KEY"):
        gemini_models = [
            "gemini/gemini-2.5-flash",
            "gemini/gemini-2.5-flash-lite",
            "gemini/gemini-2.0-flash",
            "gemini/gemini-2.0-flash-lite",
            "gemini/gemini-2.0-flash-001",
        ]
        if primary is None:
            primary = gemini_models[0]
            fallbacks.extend(gemini_models[1:])
        else:
            fallbacks.extend(gemini_models)

    # Tier 2: Groq, DeepSeek, OpenRouter (free)
    if os.getenv("GROQ_API_KEY"):
        if primary is None:
            primary = "groq/llama-3.3-70b"
        else:
            fallbacks.append("groq/llama-3.3-70b")

    if os.getenv("DEEPSEEK_API_KEY"):
        model = "deepseek/deepseek-chat"
        if primary is None:
            primary = model
        else:
            fallbacks.append(model)

    # Tier 3: Ollama (free, optional)
    if os.getenv("OLLAMA_HOST"):
        model = "ollama/llama3.1"
        if primary is None:
            primary = model
        else:
            fallbacks.append(model)

    # Tier 4: OpenAI (paid, last resort)
    if os.getenv("OPENAI_API_KEY"):
        openai_models = ["openai/gpt-4.1-nano", "openai/gpt-4o-mini"]
        if primary is None:
            primary = openai_models[0]
            fallbacks.extend(openai_models[1:])
        else:
            fallbacks.extend(openai_models)

    if primary is None:
        raise ValueError(
            "No LLM API keys configured. Set at least one of: "
            "GEMINI_API_KEY, GROQ_API_KEY, DEEPSEEK_API_KEY, "
            "OPENROUTER_API_KEY, OLLAMA_HOST, OPENAI_API_KEY"
        )

    return primary, fallbacks
