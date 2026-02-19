# **Optimization and Orchestration of Multi-Model Summarization Services: A Technical Analysis of Free-Tier Large Language Model Infrastructures**

The rapid evolution of the generative artificial intelligence landscape between 2024 and early 2026 has transitioned from a period of high-cost proprietary dominance toward the commoditization of machine intelligence. This shift is characterized by the emergence of high-performance open-weight models and the proliferation of free-access tiers provided by first-party developers, hardware-accelerated inference platforms, and third-party aggregators.1 For a specialized Python-based summarization service, such as the one currently utilizing a hardcoded dual-provider strategy with OpenAI and Google Gemini, the primary technical challenge has evolved from basic API integration to the sophisticated orchestration of heterogeneous endpoints. The objective is to maintain cost neutrality while maximizing throughput, reliability, and the preservation of structured metadata.1

The current era of "free AI" is driven by a new economic paradigm where models matching the performance of legacy frontier systems are trained at a fraction of the historical cost. For instance, the DeepSeek-V3 model demonstrated the ability to match GPT-4 class reasoning with a training budget of approximately $5.6 million, representing a 100-fold increase in efficiency compared to previous industry benchmarks.1 This efficiency has allowed providers to offer generous free tiers as a means of ecosystem acquisition, creating a diverse but fragmented market of available endpoints.

## **The Global Landscape of Free Large Language Model API Providers**

The modern developer has access to three distinct categories of free API providers: first-party laboratories, hardware-focused inference engines, and unified model aggregators. Each category offers unique advantages in terms of context window capacity, request-per-day (RPD) limits, and raw inference speed.4

### **First-Party Gateways and Developer Studios**

Google AI Studio remains the preeminent workhorse for high-volume tasks that require massive context handling, such as the summarization of long-form documents or entire codebases.1 Its flagship models, particularly the Gemini 2.5 and 3.x Flash series, are specifically designed to balance intelligence with efficient processing.7 However, the landscape of these free tiers is increasingly volatile. In December 2025, Google implemented significant quota reductions, slashing Gemini 2.5 Flash daily requests by as much as 92% in certain regions and removing free access to the "Pro" variant entirely.2 This volatility necessitates a diversified multi-provider architecture that can shift workloads dynamically when first-party limits are exhausted.1

GitHub Models serves as a critical entry point for developers already entrenched in the Microsoft ecosystem. By offering access to models like GPT-5, Grok, and DeepSeek via an integrated platform, it simplifies key management but imposes strict limitations on context size, often capping input and output at 8,000 and 4,000 tokens respectively.4 This makes GitHub Models highly effective for summarizing short documents but less suitable for the comprehensive analysis of lengthy manuscripts.4

| Provider | Primary Advantage | Rate Limit Dimension | Context Capacity |
| :---- | :---- | :---- | :---- |
| Google AI Studio | 1M+ Context Window | 5-30 RPM / 250-1,000 RPD | 1,048,576 tokens 8 |
| GitHub Models | Integrated Ecosystem | Tier-based / Low context | 8,000 tokens 2 |
| Mistral AI | 1B Tokens/Month | 1 Request / Second | 32K \- 128K tokens 2 |
| NVIDIA NIM | NVIDIA Ecosystem | 40 Requests / Minute | Model-limited 2 |

### **Hardware-Accelerated Inference Platforms**

A second class of providers has emerged from the hardware sector, offering free API access as a showcase for proprietary silicon. Groq, utilizing its Language Processing Unit (LPU) architecture, has established itself as the industry leader in raw inference speed, often exceeding 300 tokens per second.1 For summarization tasks where real-time responsiveness is prioritized, Groq’s free tier is indispensable, offering up to 14,400 requests per day for models like Llama 3.3 70B.4

Cerebras and SambaNova follow a similar trajectory, leveraging wafer-scale engines and reconfigurable dataflow units (RDUs) to provide high-throughput endpoints.13 Cerebras Inference is notable for maintaining 16-bit precision throughout the inference run, avoiding the accuracy loss associated with the heavy quantization often used by other providers to reduce costs.14 SambaNova Cloud provides a standard $5 free credit to new users, which translates to approximately 30 million tokens of Llama 3.1 8B usage—a substantial buffer for validating MVP (Minimum Viable Product) summarization workflows.17

### **Model Aggregators and Distribution Gateways**

OpenRouter represents the most versatile meta-layer in the current ecosystem. It acts as a distributor for dozens of underlying providers, standardizing their API formats and highlighting free variants with a :free suffix.10 While OpenRouter’s base free tier is capped at 50 requests per day, a single $10 lifetime top-up increases this limit to 1,000 requests per day, providing access to over 30 distinct free models including variants of Llama, Qwen, and Mistral.4 This makes OpenRouter the ideal "emergency fallback" in any automated summarization stack.1

## **Comparative Analysis of Model Performance for Summarization**

Effective summarization requires an LLM to excel in instruction-following, linguistic compression, and context retention. The optimal choice of model often depends on the complexity of the source material and the specific formatting requirements of the output, such as the Portugese-language NewsMetadata schema required by the current Python implementation.3

### **Frontier and Reasoning Models**

For tasks involving complex reasoning or the analysis of dense technical documentation, DeepSeek-V3 and its reasoning variant, R1, have redefined the performance-to-cost ratio. DeepSeek-V3 uses a Mixture-of-Experts (MoE) architecture that activates only 37 billion parameters per token out of a total 671 billion, allowing it to match or exceed the reasoning capabilities of GPT-4o while being significantly cheaper to serve.24 Benchmarks such as MMLU (Massive Multitask Language Understanding) show DeepSeek-V3 scoring approximately 77.9%, making it a primary candidate for high-accuracy summarization.1

Llama 3.3 70B, available through providers like Groq and Together AI, remains the general-purpose industry standard for open-weight summarization.1 It offers a 128K context window and demonstrates robust multilingual capabilities, which is critical for ensuring the fidelity of summaries translated into or generated in Portuguese.1

### **Lightweight and Fast-Inference Models**

When high-volume, low-latency summarization is required for standard news articles or blog posts, 7B to 9B parameter models offer the most efficient use of free tier resources. Meta’s Llama 3.1 8B and Google’s Gemma 2 9B are the primary contenders in this category.5 While Llama 3.1 8B is widely available across hardware-accelerated platforms, the Gemini 2.5 Flash-Lite variant provided by Google AI Studio is often the superior choice for high-throughput tasks due to its 1-million-token context window and generous 1,000 RPD limit in its free tier.8

| Model Family | Active Parameters | Context Window | Benchmark (MMLU) |
| :---- | :---- | :---- | :---- |
| DeepSeek-V3 | 37B (Active) | 128K tokens | 77.9% 1 |
| Llama 3.3 70B | 70B | 128K tokens | 77.3% 1 |
| Gemini 2.5 Flash | Not Public | 1M+ tokens | \~75% 1 |
| Llama 3.1 8B | 8B | 128K tokens | 66.7% 28 |
| Mistral 7B | 7B | 32K tokens | 60.1% 28 |

The mathematical evaluation of these models often relies on ROUGE (Recall-Oriented Understudy for Gisting Evaluation) metrics, which measure the overlap between machine-generated text and human reference summaries. Let ![][image1] be the reference summary and ![][image2] be the generated summary. ROUGE-N is calculated as:

![][image3]  
Models like Gemini 2.5 Flash and Llama 3.3 70B have shown superior performance in preserving the thematic essence of long documents while maintaining high ROUGE-L (Longest Common Subsequence) scores, indicating strong structural coherence.23

## **Orchestration Frameworks vs. Custom Intermediary Classes**

The core of the user's inquiry concerns whether to build a custom intermediary class or leverage existing frameworks to abstract model calls. An analysis of the current Python implementation reveals a manual failover strategy that iterates through a hardcoded model order and handles rate limits via regex-based wait-time extraction.3 While functional, this approach is highly fragile and lacks the scalability required to integrate the dozens of free providers identified in this research.

### **The Limitations of Custom Intermediary Classes**

Building a custom adapter class in Python requires the developer to manually implement:

1. **Provider-Specific Clients:** Individual code for OpenAI, Google GenAI, Anthropic, and other SDKs.3  
2. **Error Mapping:** Translating idiosyncratic provider errors (e.g., Google’s "GenerateRequestsPerDay" vs. OpenAI’s "rate\_limit\_exceeded") into a unified exception hierarchy.32  
3. **Schema Enforcement:** Manually modifying JSON schemas to fit different provider requirements, such as OpenAI's strict "Structured Outputs" versus Gemini's "Response Schema".3  
4. **Complex Retry Logic:** Managing exponential backoffs and cooldown periods for rate-limited keys.35

For professional development, this "hand-rolled" approach creates significant technical debt. Each time a provider updates their API or a new free tier emerges (as with the recent launch of Gemini 3), the custom class must be rewritten.33

### **The LiteLLM Ecosystem: A Unified Abstraction Layer**

LiteLLM has emerged as the definitive solution for abstracting LLM interactions in Python.38 It acts as a universal API wrapper, allowing developers to call over 100 different models using the standardized OpenAI request/response format.39

For the Summarizer class, LiteLLM provides several critical advantages:

* **Unified completion() Function:** A single call handles all underlying providers. Switching from Gemini to Groq requires changing only the model string (e.g., model="groq/llama-3.3-70b").39  
* **Built-in Fallbacks and Retries:** Instead of the manual while True loop found in the current script, LiteLLM allows the definition of a fallbacks list directly in the completion call. If the primary model hits a rate limit or a 500 error, the library automatically and transparently attempts the next model in the chain.35  
* **Router Class for Load Balancing:** For developers utilizing multiple free API keys to maximize RPD, LiteLLM’s Router can load-balance across these keys and implement "cooldown" periods for models that have reached their limits.32  
* **Structured Output Standardization:** LiteLLM can enforce Pydantic-based schemas across all providers, even those that do not natively support strict JSON schemas, by performing client-side validation.33

### **Framework Comparison: LiteLLM, LangChain, and Haystack**

While LiteLLM focuses on the API gateway and model abstraction layer, other frameworks address broader application logic.

| Framework | Core Design Priority | Recommended Use Case |
| :---- | :---- | :---- |
| **LiteLLM** | API Abstraction & Reliability | Multi-model failover, cost arbitrage, simplified integration.38 |
| **LangChain** | Agentic Workflows | Complex, multi-step chains involving external tools and memory.38 |
| **Haystack** | Production RAG Pipelines | High-scale document retrieval and search-centric applications.45 |
| **Instructor** | Data Extraction | Ensuring LLM output matches a specific Pydantic schema.48 |

For a summarization class that primarily needs to call various models and ensure they return a valid NewsMetadata object, LiteLLM paired with the Instructor library is the most efficient and maintainable architecture.48

## **Technical Implementation of Structured Summarization**

The user's current script uses Pydantic to define a NewsMetadata schema forPortuguese-language summaries.3 Achieving this across heterogeneous providers requires advanced handling of "Structured Outputs."

### **Schema Enforcement Across Providers**

OpenAI models natively support "Structured Outputs" with strict: True, which guarantees that the model's output will exactly match the provided JSON schema.3 Google Gemini models offer a similar response\_schema parameter in their GenerationConfig.33 However, many free-tier providers, particularly those hosting open-source models via Groq or Cerebras, may only support "JSON Mode," which guarantees valid JSON but not specific key-value adherence.3

The solution is the Instructor library, which integrates with LiteLLM to provide a "response\_model" keyword.48 When a model returns data that does not match the Pydantic schema, Instructor can automatically catch the validation error and send a new prompt to the model (including the error message) to request a correction.48

### **Portuguese Language and Sentiment Preservation**

Summarizing for a Brazilian audience requires models that not only understand Portuguese but can also perform sentiment and impact analysis.3 Research suggests that larger models like Llama 3.3 70B and Gemini 2.5 Flash significantly outperform smaller 8B variants in maintaining linguistic nuances and correctly identifying urgency/impact scores in Portuguese text.1 The Mixture-of-Experts (MoE) architecture used by DeepSeek and Mixtral is particularly effective here, as it allows the model to activate "expert" neurons specialized in specific linguistic patterns.24

The attention mechanism in these models is also a factor. Models using Grouped-Query Attention (GQA) and Sliding Window Attention (SWA), such as Mistral 7B, can process text faster but may have a more limited view of the overall document structure compared to the full dense attention used in Gemini models.25 For summarization, where global context is vital, models with larger effective attention windows are preferred.52

## **Strategies for Optimizing Free Tier Utilization**

To build a truly resilient summarization service, the architecture must transition from a simple list of models to a policy-driven orchestration system.

### **Defining Intelligent Fallback Chains**

A recommended fallback strategy for the "Daily Scribe" application should prioritize providers based on their current reliability and context capabilities.

1. **Primary Provider: Google AI Studio (Gemini 2.5 Flash).** Its 1M-token context window is the industry benchmark for summarization, though its daily limit is now a significant constraint.7  
2. **Performance Fallback: Groq (Llama 3.3 70B).** When speed is prioritized and the document is under 128K tokens, Groq’s high RPM and RPD limits make it the most reliable backup.1  
3. **Accuracy Fallback: DeepSeek (V3/R1).** For technical or academic papers where reasoning depth is paramount, DeepSeek’s MoE architecture provides superior fidelity.24  
4. **Massive-Scale Fallback: OpenRouter Free Models.** Aggregating 30+ models, OpenRouter can serve as the ultimate buffer against total service failure.19

Using LiteLLM, this chain is implemented as:

Python

from litellm import Router

model\_list \= \[  
    {"model\_name": "scribe-summarizer", "litellm\_params": {"model": "gemini/gemini-2.5-flash"}},  
    {"model\_name": "scribe-summarizer", "litellm\_params": {"model": "groq/llama-3.3-70b"}},  
    {"model\_name": "scribe-summarizer", "litellm\_params": {"model": "deepseek/deepseek-chat"}},  
\]

router \= Router(model\_list=model\_list, fallbacks=\[{"scribe-summarizer": \["openrouter/free-models-router"\]}\])

### **Rate Limit Mitigation and Token Optimization**

Efficient summarization involves managing the "token tax" of repetitive prompts. Many modern providers now support "Prompt Caching," where frequently used system instructions or context are stored on the server.53 While free tiers often exclude caching, using a provider like DeepSeek can reduce costs for the "Paid Tier" if usage ever scales, with cache hits costing as little as $0.028 per million tokens.24

For the current Portuguese extraction task, developers can also use "FreeFlow," a Python wrapper specifically designed to rotate multiple API keys to maximize free tier RPD.56 By cycling through five separate Gemini API keys, for example, a developer can effectively increase their daily limit from 250 to 1,250 requests.11

### **Context Window and Document Management**

The effective "working memory" of an LLM is limited by its context window.52 For a professional summarizer, the document size must be matched to the model’s capacity to avoid truncation or the "lost-in-the-middle" effect, where models fail to recall information from the center of a long prompt.

| Task Profile | Word Count | Token Count | Recommended Model Tier |
| :---- | :---- | :---- | :---- |
| News Articles | 500 \- 1,500 | 650 \- 2,000 | 8K \- 32K Context 52 |
| Research Papers | 5,000 \- 10,000 | 6,500 \- 13,000 | 32K+ Context 52 |
| Books/Full Codebases | 80,000+ | 100K+ | 128K \- 1M Context 52 |

## **Local Inference as a Reliability Buffer**

When cloud-based free tiers are unavailable or privacy is a paramount concern, running models locally on consumer hardware provides a stable baseline for summarization.60

### **Ollama: The Local LLM Gateway**

Ollama allows for the local execution of open-source models like Llama 3.1 8B, Mistral, and DeepSeek-V3.60 It provides a local API server that mimics the OpenAI format, making it compatible with the same LiteLLM abstraction layer used for cloud models.41

The primary trade-off for local inference is performance. On standard consumer hardware, an 8B model might take 10-30 seconds to generate a summary, whereas cloud-based LPUs (like Groq) do so in milliseconds.60 Furthermore, running a 70B model locally requires significant VRAM (approximately 40GB with Q4 quantization), making it inaccessible for developers without high-end GPUs like the RTX 4090 or Mac M2/M3 Max.52

### **Implementing Local-Cloud Hybrid Orchestration**

The most robust architecture for the Summarizer class is a hybrid model. LiteLLM can be configured to use local Ollama models as the "Emergency Fallback" of last resort.60 This ensures that even in the event of a total internet failure or a global API outage, the Portuguese news summarization service remains operational.

## **Comparative Benchmarking for Advanced Tasks**

A critical component of a professional-grade summarizer is understanding where specific models excel beyond general text generation.

### **Mathematical and Algorithmic Reasoning**

While the user's primary task is Portuguese news summarization, the "Deep Research" capabilities of models like Gemini 2.0 Flash and DeepSeek R1 are valuable for extracting quantitative data (e.g., economic figures, urgency scores).7 In 2025 benchmarks, DeepSeek-V3.2 demonstrated a 96.0% score on AIME (American Invitational Mathematics Examination), outperforming legacy frontier models.24 This architectural depth translates into more accurate "Urgency" and "Impact" scores in the NewsMetadata schema, as the model can better "reason" about the consequences of reported events.3

### **Coding and Agentic Performance**

The "Daily Scribe" application may require agentic behavior—for instance, the ability for the summarizer to search the web for corroborating information. Llama 4 Scout and Claude 3.7 Sonnet are emerging as the leaders in "Agentic Coding" and tool-use, scoring highly on SWE-bench (Software Engineering Benchmark).1 Gemini 3 Pro also features a "Thinking Mode" designed specifically for multi-step reasoning tasks.7

## **The Evolution of Structured Output Standards**

The industry is moving toward "native" JSON schema support. Gemini 2.0+ models now use a native responseJsonSchema parameter that is fully compatible with standard JSON schemas, eliminating the need for complex property-ordering hacks previously required in Gemini 1.5.33

For the user's Python script, this means that the \_enforce\_no\_additional\_properties helper method may become obsolete as models natively adopt Pydantic-friendly formats.3 LiteLLM manages this transition by automatically mapping Pydantic's model\_json\_schema() to the appropriate native provider parameter.33

## **Strategic Implementation Recommendations**

Based on the exhaustive research of the 2025-2026 LLM landscape, the path forward for the Portuguese summarization service is clear. The developer should prioritize the replacement of the hardcoded Summarizer class logic with a framework-driven orchestration layer.

### **Phase 1: Infrastructure Modernization**

The first step is the adoption of LiteLLM and Instructor. This will immediately reduce the complexity of the Python script by removing the need for manual retry loops and hardcoded API clients.38 By defining a Router that incorporates Google, Groq, and OpenRouter, the service gains immediate resilience to rate limit changes.36

### **Phase 2: Provider Diversification**

The developer should register for free-tier access with the following "Top 5" providers for 2026:

* **Google AI Studio:** For long-document context.8  
* **Groq:** For high-speed news summaries.2  
* **Cerebras:** For high-accuracy 16-bit inference.14  
* **SambaNova:** For high-throughput Llama 3.3 70B access.15  
* **OpenRouter:** As the comprehensive meta-layer fallback.19

### **Phase 3: Metadata and Quality Optimization**

Using the Instructor library, the NewsMetadata schema can be enforced across all these providers.49 This ensures that the Portuguese summaries, sentiment analysis, and geographic tagging are consistent regardless of which model (Gemini, Llama, or DeepSeek) ultimately processes the request.3

## **Conclusion**

The democratization of AI through free API tiers has created an unprecedented opportunity for developers to build high-scale applications with minimal infrastructure costs. However, the volatility of these tiers requires a shift in architectural philosophy from "model-centric" to "orchestration-centric." By leveraging LiteLLM as an abstraction layer and diversifying across hardware-accelerated and first-party providers, the Portuguese summarization service can achieve enterprise-grade reliability and performance. The key to long-term success in this environment is the ability to adapt to a landscape where the "best" model or provider may change on a weekly basis, and where the ultimate goal is the seamless delivery of machine intelligence as a utility.1

#### **Referências citadas**

1. Best Free AI APIs for 2025: Build with LLMs Without Spending a Penny \- MadAppGang, acessado em fevereiro 18, 2026, [https://madappgang.com/blog/best-free-ai-apis-for-2025-build-with-llms-without/](https://madappgang.com/blog/best-free-ai-apis-for-2025-build-with-llms-without/)  
2. Best Gemini API Alternatives with Free Tier \[2025 Complete Guide\], acessado em fevereiro 18, 2026, [https://www.aifreeapi.com/en/posts/best-gemini-api-alternative-free-tier](https://www.aifreeapi.com/en/posts/best-gemini-api-alternative-free-tier)  
3. summarizer.py  
4. cheahjs/free-llm-api-resources \- GitHub, acessado em fevereiro 18, 2026, [https://github.com/cheahjs/free-llm-api-resources](https://github.com/cheahjs/free-llm-api-resources)  
5. 15 Free LLM APIs You Can Use in 2026 \- Analytics Vidhya, acessado em fevereiro 18, 2026, [https://www.analyticsvidhya.com/blog/2026/01/top-free-llm-apis/](https://www.analyticsvidhya.com/blog/2026/01/top-free-llm-apis/)  
6. Google AI Studio Free Plans and Trials: access tiers, usage limits, and upgrade paths in late 2025, acessado em fevereiro 18, 2026, [https://www.datastudios.org/post/google-ai-studio-free-plans-and-trials-access-tiers-usage-limits-and-upgrade-paths-in-late-2025](https://www.datastudios.org/post/google-ai-studio-free-plans-and-trials-access-tiers-usage-limits-and-upgrade-paths-in-late-2025)  
7. Gemini Apps limits & upgrades for Google AI subscribers, acessado em fevereiro 18, 2026, [https://support.google.com/gemini/answer/16275805?hl=en](https://support.google.com/gemini/answer/16275805?hl=en)  
8. Gemini Developer API pricing, acessado em fevereiro 18, 2026, [https://ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing)  
9. Gemini free tier rate limits slashed again : r/Bard \- Reddit, acessado em fevereiro 18, 2026, [https://www.reddit.com/r/Bard/comments/1lj4wdp/gemini\_free\_tier\_rate\_limits\_slashed\_again/](https://www.reddit.com/r/Bard/comments/1lj4wdp/gemini_free_tier_rate_limits_slashed_again/)  
10. Summary of some free LLMs APIs providers \- 2coffee.dev, acessado em fevereiro 18, 2026, [https://2coffee.dev/en/articles/free-llms-api-providers-summary](https://2coffee.dev/en/articles/free-llms-api-providers-summary)  
11. Interpreting Google AI Studio Rate Limits 2026 Latest Version: What to Do if Tier 1 RPD 250 is Too Strict, acessado em fevereiro 18, 2026, [https://help.apiyi.com/en/google-ai-studio-rate-limits-2026-guide-en.html](https://help.apiyi.com/en/google-ai-studio-rate-limits-2026-guide-en.html)  
12. Rate limits | Gemini API \- Google AI for Developers, acessado em fevereiro 18, 2026, [https://ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits)  
13. Pricing \- Cerebras, acessado em fevereiro 18, 2026, [https://www.cerebras.ai/pricing](https://www.cerebras.ai/pricing)  
14. Cerebras Launches the World's Fastest AI Inference, acessado em fevereiro 18, 2026, [https://www.cerebras.ai/press-release/cerebras-launches-the-worlds-fastest-ai-inference](https://www.cerebras.ai/press-release/cerebras-launches-the-worlds-fastest-ai-inference)  
15. Rate Limits Policy \- SambaNova Documentation, acessado em fevereiro 18, 2026, [https://docs.sambanova.ai/docs/en/models/rate-limits](https://docs.sambanova.ai/docs/en/models/rate-limits)  
16. Announcing Native Support for Cerebras Inference in Vellum, acessado em fevereiro 18, 2026, [https://www.vellum.ai/blog/announcing-native-support-for-cerebras-inference-in-vellum](https://www.vellum.ai/blog/announcing-native-support-for-cerebras-inference-in-vellum)  
17. Plans \- SambaNova Cloud, acessado em fevereiro 18, 2026, [https://cloud.sambanova.ai/plans](https://cloud.sambanova.ai/plans)  
18. SambaNova Cloud Developer Tier Is Live\!, acessado em fevereiro 18, 2026, [https://sambanova.ai/blog/sambanova-cloud-developer-tier-is-live](https://sambanova.ai/blog/sambanova-cloud-developer-tier-is-live)  
19. Free Models Router | Zero-Cost AI Inference | OpenRouter | Documentation, acessado em fevereiro 18, 2026, [https://openrouter.ai/docs/guides/routing/routers/free-models-router](https://openrouter.ai/docs/guides/routing/routers/free-models-router)  
20. OpenRouter Review 2025: Unified AI Model API, Pricing & Privacy, acessado em fevereiro 18, 2026, [https://skywork.ai/blog/openrouter-review-2025-unified-ai-model-api-pricing-privacy/](https://skywork.ai/blog/openrouter-review-2025-unified-ai-model-api-pricing-privacy/)  
21. They removed the Free Tier for 2.5 Pro API. : r/Bard \- Reddit, acessado em fevereiro 18, 2026, [https://www.reddit.com/r/Bard/comments/1pg02ni/they\_removed\_the\_free\_tier\_for\_25\_pro\_api/](https://www.reddit.com/r/Bard/comments/1pg02ni/they_removed_the_free_tier_for_25_pro_api/)  
22. Top Free Text Summarization tools, APIs, and Open Source models \- Eden AI, acessado em fevereiro 18, 2026, [https://www.edenai.co/post/top-free-summarization-tools-apis-and-open-source-models](https://www.edenai.co/post/top-free-summarization-tools-apis-and-open-source-models)  
23. Text Summarization for NLP: 5 Best APIs, AI Models, and AI Summarizers in 2025, acessado em fevereiro 18, 2026, [https://www.assemblyai.com/blog/text-summarization-nlp-5-best-apis](https://www.assemblyai.com/blog/text-summarization-nlp-5-best-apis)  
24. DeepSeek-V3.2 Matches GPT-5 at 10x Lower Cost | Introl Blog, acessado em fevereiro 18, 2026, [https://introl.com/blog/deepseek-v3-2-open-source-ai-cost-advantage](https://introl.com/blog/deepseek-v3-2-open-source-ai-cost-advantage)  
25. Mistral vs Llama 3: Complete Comparison for Voice AI Applications \- Vapi AI Blog, acessado em fevereiro 18, 2026, [https://vapi.ai/blog/mistral-vs-llama-3](https://vapi.ai/blog/mistral-vs-llama-3)  
26. Top 10 open source LLMs for 2025 \- NetApp Instaclustr, acessado em fevereiro 18, 2026, [https://www.instaclustr.com/education/open-source-ai/top-10-open-source-llms-for-2025/](https://www.instaclustr.com/education/open-source-ai/top-10-open-source-llms-for-2025/)  
27. What are good models for summarizing an article that are available as a low cost API endpoint? : r/ChatGPTCoding \- Reddit, acessado em fevereiro 18, 2026, [https://www.reddit.com/r/ChatGPTCoding/comments/1bo6v8t/what\_are\_good\_models\_for\_summarizing\_an\_article/](https://www.reddit.com/r/ChatGPTCoding/comments/1bo6v8t/what_are_good_models_for_summarizing_an_article/)  
28. Mistral 7B Instruct vs Llama 3.1 8B Instruct \- Detailed Performance & Feature Comparison, acessado em fevereiro 18, 2026, [https://docsbot.ai/models/compare/mistral-7b-instruct/llama-3-1-8b-instruct](https://docsbot.ai/models/compare/mistral-7b-instruct/llama-3-1-8b-instruct)  
29. Llama 3.1 8B Instruct vs Mistral 7B Instruct | AIModels.fyi, acessado em fevereiro 18, 2026, [https://www.aimodels.fyi/compare/llama-3-1-8b-instruct-vs-mistral-7b-instruct](https://www.aimodels.fyi/compare/llama-3-1-8b-instruct-vs-mistral-7b-instruct)  
30. Gemini 1.5 Flash-8B vs Mistral 7B Instruct \- Detailed Performance & Feature Comparison, acessado em fevereiro 18, 2026, [https://docsbot.ai/models/compare/gemini-1-5-flash-8b/mistral-7b-instruct](https://docsbot.ai/models/compare/gemini-1-5-flash-8b/mistral-7b-instruct)  
31. LLM Leaderboard 2025 \- Vellum AI, acessado em fevereiro 18, 2026, [https://www.vellum.ai/llm-leaderboard](https://www.vellum.ai/llm-leaderboard)  
32. LiteLLM \- Getting Started, acessado em fevereiro 18, 2026, [https://docs.litellm.ai/docs/](https://docs.litellm.ai/docs/)  
33. Gemini \- Google AI Studio \- LiteLLM, acessado em fevereiro 18, 2026, [https://docs.litellm.ai/docs/providers/gemini](https://docs.litellm.ai/docs/providers/gemini)  
34. Structured Outputs (JSON Mode) \- LiteLLM, acessado em fevereiro 18, 2026, [https://docs.litellm.ai/docs/completion/json\_mode](https://docs.litellm.ai/docs/completion/json_mode)  
35. Reliability \- Retries, Fallbacks \- LiteLLM Docs, acessado em fevereiro 18, 2026, [https://docs.litellm.ai/docs/completion/reliable\_completions](https://docs.litellm.ai/docs/completion/reliable_completions)  
36. Fallbacks \- LiteLLM, acessado em fevereiro 18, 2026, [https://docs.litellm.ai/docs/proxy/reliability](https://docs.litellm.ai/docs/proxy/reliability)  
37. Accelerating GenAI: Is LiteLLM Enough or Should You Build an AI Orchestrator? \- Medium, acessado em fevereiro 18, 2026, [https://medium.com/@anuj.sadani/accelerating-genai-is-litellm-enough-or-should-you-build-an-ai-orchestrator-a926f40cd5a4](https://medium.com/@anuj.sadani/accelerating-genai-is-litellm-enough-or-should-you-build-an-ai-orchestrator-a926f40cd5a4)  
38. Langchain vs LiteLLM. I understand that learning data science… | by ..., acessado em fevereiro 18, 2026, [https://medium.com/@heyamit10/langchain-vs-litellm-a9b784a2ad1a](https://medium.com/@heyamit10/langchain-vs-litellm-a9b784a2ad1a)  
39. Unlocking the Power of LiteLLM: A Lightweight, Unified Interface for LLMs | by Hajraali, acessado em fevereiro 18, 2026, [https://medium.com/@hajraali730/unlocking-the-power-of-litellm-a-lightweight-unified-interface-for-llms-5dc09cece265](https://medium.com/@hajraali730/unlocking-the-power-of-litellm-a-lightweight-unified-interface-for-llms-5dc09cece265)  
40. Is LiteLLM the Easiest Way to Talk to Every LLM? A Practical Review \- Sider.AI, acessado em fevereiro 18, 2026, [https://sider.ai/blog/ai-tools/is-litellm-the-easiest-way-to-talk-to-every-llm-a-practical-review](https://sider.ai/blog/ai-tools/is-litellm-the-easiest-way-to-talk-to-every-llm-a-practical-review)  
41. BerriAI/litellm: Python SDK, Proxy Server (AI Gateway) to ... \- GitHub, acessado em fevereiro 18, 2026, [https://github.com/BerriAI/litellm](https://github.com/BerriAI/litellm)  
42. LiteLLM: A Guide With Practical Examples \- DataCamp, acessado em fevereiro 18, 2026, [https://www.datacamp.com/tutorial/litellm](https://www.datacamp.com/tutorial/litellm)  
43. Router \- Load Balancing | liteLLM, acessado em fevereiro 18, 2026, [https://docs.litellm.ai/docs/routing](https://docs.litellm.ai/docs/routing)  
44. Routing, Loadbalancing & Fallbacks \- LiteLLM, acessado em fevereiro 18, 2026, [https://docs.litellm.ai/docs/routing-load-balancing](https://docs.litellm.ai/docs/routing-load-balancing)  
45. What are the differences between LangChain and other LLM frameworks like LlamaIndex or Haystack? \- Milvus, acessado em fevereiro 18, 2026, [https://milvus.io/ai-quick-reference/what-are-the-differences-between-langchain-and-other-llm-frameworks-like-llamaindex-or-haystack](https://milvus.io/ai-quick-reference/what-are-the-differences-between-langchain-and-other-llm-frameworks-like-llamaindex-or-haystack)  
46. Haystack vs LangChain: Explained \- Peliqan, acessado em fevereiro 18, 2026, [https://peliqan.io/blog/haystack-vs-langchain/](https://peliqan.io/blog/haystack-vs-langchain/)  
47. LangChain vs Haystack: Which Framework Should You Choose? \- Leanware, acessado em fevereiro 18, 2026, [https://www.leanware.co/insights/langchain-vs-haystack](https://www.leanware.co/insights/langchain-vs-haystack)  
48. litellm/docs/my-website/docs/tutorials/instructor.md at main \- GitHub, acessado em fevereiro 18, 2026, [https://github.com/BerriAI/litellm/blob/main/docs/my-website/docs/tutorials/instructor.md](https://github.com/BerriAI/litellm/blob/main/docs/my-website/docs/tutorials/instructor.md)  
49. Instructor \- Multi-Language Library for Structured LLM Outputs | Python, TypeScript, Go, Ruby \- Instructor, acessado em fevereiro 18, 2026, [https://python.useinstructor.com/](https://python.useinstructor.com/)  
50. Instructor vs. LiteLLM Comparison \- SourceForge, acessado em fevereiro 18, 2026, [https://sourceforge.net/software/compare/Instructor-LLM-vs-LiteLLM/](https://sourceforge.net/software/compare/Instructor-LLM-vs-LiteLLM/)  
51. Structured outputs with LiteLLM, a complete guide w \- Instructor, acessado em fevereiro 18, 2026, [https://python.useinstructor.com/integrations/litellm/](https://python.useinstructor.com/integrations/litellm/)  
52. Context Length Guide 2025: Master AI Context Windows for Optimal Performance & Results, acessado em fevereiro 18, 2026, [https://local-ai-zone.github.io/guides/context-length-optimization-ultimate-guide-2025.html](https://local-ai-zone.github.io/guides/context-length-optimization-ultimate-guide-2025.html)  
53. Models & Pricing \- DeepSeek API Docs, acessado em fevereiro 18, 2026, [https://api-docs.deepseek.com/quick\_start/pricing](https://api-docs.deepseek.com/quick_start/pricing)  
54. Pricing \- OpenRouter, acessado em fevereiro 18, 2026, [https://openrouter.ai/pricing](https://openrouter.ai/pricing)  
55. LLM API Pricing Comparison (2025): OpenAI, Gemini, Claude \- IntuitionLabs.ai, acessado em fevereiro 18, 2026, [https://intuitionlabs.ai/articles/llm-api-pricing-comparison-2025](https://intuitionlabs.ai/articles/llm-api-pricing-comparison-2025)  
56. I built a wrapper to get unlimited free access to GPT-4o, Gemini 2.5, and Llama 3 (16k+ reqs/day) : r/Python \- Reddit, acessado em fevereiro 18, 2026, [https://www.reddit.com/r/Python/comments/1q87ngh/i\_built\_a\_wrapper\_to\_get\_unlimited\_free\_access\_to/](https://www.reddit.com/r/Python/comments/1q87ngh/i_built_a_wrapper_to_get_unlimited_free_access_to/)  
57. Most powerful LLMs (Large Language Models) in 2025 \- Codingscape, acessado em fevereiro 18, 2026, [https://codingscape.com/blog/most-powerful-llms-large-language-models](https://codingscape.com/blog/most-powerful-llms-large-language-models)  
58. LLMs with largest context windows \- Codingscape, acessado em fevereiro 18, 2026, [https://codingscape.com/blog/llms-with-largest-context-windows](https://codingscape.com/blog/llms-with-largest-context-windows)  
59. LLM Usage Limits 2026: ChatGPT vs. Claude vs. Gemini (Full Comparison), acessado em fevereiro 18, 2026, [https://exploreaitogether.com/llm-usage-limits-comparison/](https://exploreaitogether.com/llm-usage-limits-comparison/)  
60. Ollama Review 2026: Pros, Cons, Pricing & Alternatives \- Elephas, acessado em fevereiro 18, 2026, [https://elephas.app/blog/ollama-review](https://elephas.app/blog/ollama-review)  
61. Ollama vs vLLM: A Comprehensive Guide to Local LLM Serving | by Mustafa Genc \- Medium, acessado em fevereiro 18, 2026, [https://medium.com/@mustafa.gencc94/ollama-vs-vllm-a-comprehensive-guide-to-local-llm-serving-91705ec50c1d](https://medium.com/@mustafa.gencc94/ollama-vs-vllm-a-comprehensive-guide-to-local-llm-serving-91705ec50c1d)  
62. Pricing \- Ollama, acessado em fevereiro 18, 2026, [https://ollama.com/pricing](https://ollama.com/pricing)  
63. Running Local LLMs with Ollama: 3 Levels from Laptop to Cluster-Scale Distributed Inference \- BentoML, acessado em fevereiro 18, 2026, [https://www.bentoml.com/blog/running-local-llms-with-ollama-3-levels-from-local-to-distributed-inference](https://www.bentoml.com/blog/running-local-llms-with-ollama-3-levels-from-local-to-distributed-inference)  
64. Models | Machine Learning Inference \- Deep Infra, acessado em fevereiro 18, 2026, [https://deepinfra.com/models](https://deepinfra.com/models)  
65. LiteLLM \- Gemini by Example, acessado em fevereiro 18, 2026, [https://geminibyexample.com/033-litellm/](https://geminibyexample.com/033-litellm/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAAYCAYAAAB0kZQKAAABbUlEQVR4Xu2WvytFYRjHH782kfwJSixsJpmsLBZ/AGUSdS2S0SLJoEjqlpkysVmMDCxKRoMYkFF+fJ/7npfn/Z7TkXvve1A+9eme+33fznl67nPfjsg/f4RuuAlHTFYy11Fpga9wC7bBIfgGF+CT2RcVfeAgh+LyeQ5jUBb3sCw01y5FRx+UV0Qh+CJWeKFIluWzEO9GsKMgpiVdyGWwo3ZaOchjWPLn5Ls0wBt4DztprcIYBwk7Ur8i1uGsuG6nGIUzHCbMSf2K0Pt0cOg5hXscJrxIOJxn8Bn2wH14YdYW4RU8ge0m15PXztiRWfvAL/LA7Er6qO6DD+JaOi6uIOUcTvhN4o55Jrej17BR3M11ow6OfpbNHgvfrCnJDuEtXAqXK/TDRw5rgYsYyMiYNbjKYbVMwgMOJSyiGW6b74p2oZeyqjkW967BTME7cT+lzgrzVaeiooOs6DvKj6Ed0M508UKR6D8n84j+VbwD9E9U2W782n0AAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAYCAYAAACfpi8JAAABhUlEQVR4Xu2VTShEURTHTz428rEh9iTK0hIrCwkpGyubUbKR8rGQpZ0sFSkmUhaoWbKzVcxiFiOlFEvyvZGv/+meO3Pe9ZrFa94V+dWvOfd/7+ue7tzeI/rnF9IMV2G/yqZVHTvl8AOuwWrYBT/hPHxS62KHN+1wQzL5nBvGRZLMhmFwzqflBd6sUCPesI0suRO+WaR8M9aVwAqPTND3Zs4DK36Abip8b2JhyA2ELfLYyACcdENhhjw2cgL33VB4p/ALewN34ChMqJxP8BhequwAZmAv3IWvsEzN57D3oNLJ9yj8ta5PiBvqkfoBtkhdReYNzd8rhp+pk3odTkkd4BqWwHsyD9zJb1KtsfBr/kKNbVNtUh/CZziWW0HUBF/U+A02qHEkHuGwGttGZuGVyjXbZD6alqLcuSPK/xUpeCp1K5mTtNTCEal5Y/udGoRp2AgrJIsMX0b2DPapfBlmyZxau8r5clpKycwvqCwSNaouyhFHYRzeSr0JN9Scd+phpxv+Gb4A3s1bubvG0rQAAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAAA8CAYAAADbhOb7AAAOT0lEQVR4Xu3dC9Bu1RzH8eWuKN1QklNKjFvJbWqSmpJkopSu0gmD7sWUS2kOohhKZDAuMxlSQim6KDqpKJREpItOEypdJZEK69de/3n/z/9d+7mc87zv2c97vp+ZNc9a/72fZz/7OWfOXmft/1o7JQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAhHhDLjvlsksuu+ayW58yabZPzbntnAaf2+PLe4Bxe1MMAAAwqu/l8r8YDLZNzT6fjRs67j9p8LkdmZp9HowbJtCPU3MuKuqAPzaXFXv2mJvOiYEOOiIGAAAYlS7wf4/BikGdny66LQ33ve+NgQmyKE0/xydXYjNlto5TszSPPYqfxQAAAItDF77XxOAcoXNbGIMVT4uBCXBGLvfFYDEbnZlHp9k5TpszY6DD/hUDAACM6vdp6V54Z9L8NHfPrd95PRwDM2C/XL4bg7PkgFw2i8EO6/dnBQDA0HRBuTYG54hh8tkmzbfS8Of09NSMxC2Xy4tz+UWJ35jLBbk8sbS/nZqJGnJKLmvmclGaGqG0462Wy3tKW68qs62tQ6rvpI7cRqUui1JzXjrXZ+Ryf4kb20+vVj8pl5VK+x63fYVcPpTLk0p7WKPsCwBAX7qoPDsG5wid2+djcILpfK6OwRaxs6D25q7u40aTGDR54c8uVvucJfWnGHD6TXSpHVuxJ4S2HJXL13M5obT/UV7Ff87JuXyg1C/OZY/Uu105kQe7du07tBllXwAA+tIoxIUx2Md65VUjN4O8N5drYnAxLcjllzE4gJbueCgGO2ytGAjUAdgnBovfuvo/cznataWtkxY7FWprJMm3vdheHP+NAaff59e2+dhjQru2/1NT/33U9jOI/fYtcrnJtQeJnw0AwGIbZXkLjVqYK1y9ZtU0/YL1Q1eP24Yx6kjgKOe2tGkkR2q/m1mYmtzDGr/2V3z/obncXOqvTVOdOz+BYMfy6t97SS575bJpae+fmkkPclZqlhDZIZcbSkwjWo9KzSiVsduY9rmrpGYdPHWuxG5V2vb46g2KnZuaPDdT21//ibjFtW2fDV17m1K3dqzr1rSNul1WXmud0NrxAQAYWVtOUM2nQvsprq5Rh3VT76zLZ6bpFyzf/qSrD0u5SI+LwRY/jYGO0MzBF+ayuospb2oT1+732+g3fJFrKxftm64tusX3tlLXdv+76ze8q9TVyTgx9eYx1joo1tnTCKdGWF9R2vIXV59fXu37qKNno4bWMTu2vIo6bvNcW3RLVuLfHVGOWVzw2PZbw9VNbBuL67xV99/Bv0f/QfAzcm3b3uX1HbYh+4Orm7bjAwAwtEtjoEKdLmMXfhWN2Ji2pUFekHrzhkQXbb3/8hAflkZn1LkZRKNNGukZRGuXyb6p2d/WZntWakbnDkpNXpfYxddetY+Ndi3I5apSP7u81tweA479tr7z0EYjWJosYPlZNbqt+cbULKYbaULCy0pdnUdPv7H3qtDeLrTt9/hwiG2eepdWeXUuG5Rt8rxczpva/Mj39B3V96VmxC7qN0M1dpD6de5tooX+Xq/s4vH8PX3e2q5tx3t9eY3LxIwrHQAAsIzaPQZaxAugxDwhjRj5IroQ+9tiUe32UfSJVJ/BekwuX45BRx2Vl8RgYDMBTeyMyStd3a9af76r26iYH83rt8L9A2n6bxXVfvMuO668+tvP6qhrxEv+mJqOv3XS1QFeWOqi0b6/lbo/97ZOvd/HRgpFs0T9ZInZYN97/TR9IoXvjAIAMDItUaDRrxot3bB1ap6CoAujjZpYvpHxF82NXd1TTtCdrq1lNox12L6fy8dS8wxQa4u+o45heUVGOVNxFMPTraqvxGCxfGrysfS5Kn6ZB1uiws5Lt94861ytk5oZicr98vvY+/ytSeV4fdW15Y7QNj7J/9eujjrlkIl+dy2kq1flr3XJYTEAAF2ndZ10odI/qsqZurvU2x6NpPWP7AKq5Ojj3bZFaeqCq8/aqsT1P12LxxwX3cZQ/GupuZ2h4+qi/xm3j9j7a2Xcbk31z7aY79yM27tzOTA1SdO2npbKIam5BahtSi7XAqnmB6lJrlYnJc4+FHVMfKdD9Ofuz0+34K5LzQxGY3/OohGa0137VFc3yr+KnUdPMyiVdD7o3HQL1M9yVedKMcvTi38uOqbWMVOnz5LMbR/lOdlkCh3/ylK37VoDzVPOlzrGRr/L4anpeIwyW3dZNszt7qVJf5cAYGLFi6DaXwox3TJSbosX36dbJTEmtZgoPq8S8xdNU/uMWmwcdDtHn61OgKck8EmkUSdbjFWUJzXot/MjcH4Gqmg2YxT/HMdJHUzLaRsH5QjqPwt+jTDP/1YAAHRGvHgrAdvHVK+N3mhUxj9IWfvFz5La7SbtV7sw1t6vkY5avBYbB430Kfdppj6/Cwadm59pOozrY2AMlA/3o1w+EjcAALCs2TlNv3irbYnJuqVpM/Si36TpHTtbmdyLeVm69dSW3B6/i6gD5ROd31peffL5OL20vPrvEnOnllVti8MCAIAZpE6JZvwpj+xXufy7d/Mj22PumdE25XyJ8o5qna35oa3Ze9pPyevD0v6+zCSf16Rj2QjioOPeOKCcNrUrAADAaGJHZFDb0zZLaNctxLi2l8T3K0k+xjSat2Vq1oOyyQqe398vgtmW4KxbqG1FyfH9+NwtdVTt2JoxOVN0DAqFsvQKAHSacoTiP1aD2kYLZ/ptqteS0X8X2h9N7Z9Zi2tpilr80zEwJrHTqWNrsVcAAIClIv7v0j+/0KituNe2n1aY97Tie432nRdieqRP/EzRUhO1B4vPxEKcWsE9rh6vxwjVvhcAAMCM0tpVWgRUHZGH0tQjfsQ6J7bemB5Lo5ity6XlPvxtSU/76XFIWjaibbV4o32/U+rvT80jhDSJweyZmvW1tJ9WKv9JLheV9kx0oHQM++znhG0zcbxxse88TNmpvGdS6PFS8Rzaij00HeMT81m7Jo6GAwDQaeqwxDXyog+mZr9Jo+8cn0oQ6Zmbk3hu3rCLSM8W/0ivLmt7TBYAAJ3zujRch0UPHJ809nzUfg8LF21fNQYnxEap/udXi82EeBw9VWJSOmwxRxYAgE7TRXdhDFb0e95nV+nc2tbt894cAxNC51d7kkPsSM2UeBy1Y95qV2mW+oIYBACgy3ShvSkG5widm3++6VyhRaSVR1oTO1KiHFH/IHvRA9dXcu3nu7pyTm3pnQWp9xbrNrnsnZpctW1dvHZcYw93N8px1TNw5dg0veOpSTvHhZjec2Sp67ue4LbtlabvP0i/7wsAQOcclpqLl79gzxWrpLl5YdY56bbvMPz5W/2sXHZv2fZO196x1NdNzQQboyeZaIa2V7vNeHAux5e6Opk3lvrpuZyXmhFQy8MzsW5PENF79Mgx31HV9odLXX9/NeFkWHPx7wUAYI7TqMlcvYBdnObeuQ17PtrPP6w+doauKfWX57Ko1A8tr37f/XI507Xj8dfJ5cQQE7+fJkT4/xTEzxDNEn+Xa8d9+rU1knqqaw8SPwsAgIkwkxcw3ZIbh8XNpbsuBiZc25/VEaEd94sdNnNP6p0x/IVcjnbtfp8juqWpETBPuYFtx6u1Jcb6tbUI9wLXjvsOMur+AAAsdXfHwADqGMzL5Ya4oaJ2YdTzZ5WT9NdctgvbBtGjxfaNwT5qx++yk1JzK/fSuMHROcUFp8XnlIk/d2273bVrnSkbcfPbfMdLeWNaDkWjZeL3u9nVZetcLnDt+OcQ2+Jj66UmT86vb1j7zrGtp5nsmprveEVqFtFe03Zy4vsBAOi0US9cfn/LHxLlGim36a7UmxAeP98WV14SR8VAi3tjoCOUf3ZVan4rdS5Mvw5JpO32O6iTsqnbZtSJ0u3uA1NvDpro/W/J5fpS9zlp/tjKQ1P7stLWs3LVUV9oOxS176vY51KTM3ebi2sJkMNd2+gYum2q30YdRT2ZxBbi1Xv8CGI8nto/L3U97s62fzw1I4ZRfD8AAJ2l0YdB1g5tXej0NAmfG3WOq0fxwqgOm0Z63h7iozgmBipOjoEWGjEyGpXRKNMluayQy4Op6WzYUzpWzuUbuWxf2tpH56PHk9kTNzRC9sVSr9HoWRv9VupA6TiTRt+97db3fakZMZtN55fX+PdP1EketEYfAACdcFoMVGyY6hc8PTvVx5dzdU8zEXeJwdTcolKHyo/QtdFswkgzBVeMQWfj1NuhrNF39udgdY3s6Dm0mpFoMS1SK7b8icX9Pvo8S6qv/WbGRoHaTPITGGq/Z6zPBk2C0C13UQf4ALdNZvv7AACwWDZLTaK5bmEqj0y3nlRuzeX+1FzQrPiZd/4Wox/l0lMT2vi8KS0h4l0b2pFu9dXcGQOOFm99IDXHvSX1nps6iP7cap0KvdoIl9++Ry5rlbp+I2P7XOhiu7l6pNugNRrJM7qNOalsvbf5qenQ7jy1qRP8M5ABAOg0rbWlUQflJ2k5BF8UU86Ttms5Bz96VuvgyJWuHvn9fIdPtxO1OKtuT6kDdEcuq6VmZMxuU+oW5XNL3et3S1STGPZPzXkckqbOS3XFDkpT56aOq9HtT/Hf92xXV+6W6PdQXpQ+T84tr/Y+fa6o46gcMY3O+Ryqtue3tv22k2arGOiYTWIAAIC5xFajV4doB7+hUNxGsPyD133nY/VcNkjTE84t9yl2VPxIlrcgBsZI+Xlt1iivtUWG/UxEnafYSGB8RNbyqRnh1PnuWWKaiLBFLvvYTgAAALMldsL60S1TP1lAtyFrYk7SkjqlvF7eE11yZ5TXq3uiAAAAHaRJCqOq5a8ph2z9GAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAoCP+D9ctTLwl3OQuAAAAAElFTkSuQmCC>