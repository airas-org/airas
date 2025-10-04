MODEL_LIST = {
    "Large Language Models": {
        # Llama
        # https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E
        "Llama-4-Scout-17B-16E": "Llama 4, developed by Meta, is a new generation of natively multimodal AI models that leverage a Mixture-of-Experts (MoE) architecture to achieve state-of-the-art performance in both text and image understanding. Marking the beginning of a new era for the Llama ecosystem, the series introduces two models: Llama 4 Scout, a 17-billion-parameter model with 16 experts, and Llama 4 Maverick, also with 17 billion parameters but incorporating 128 experts. These auto-regressive language models employ early fusion to enable seamless multimodal processing, allowing them to integrate text and image information natively.",
        # https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E
        "Llama-4-Maverick-17B-128E": "The Llama 4 collection, developed by Meta, represents a new generation of natively multimodal AI models designed to enable both text and multimodal experiences. By leveraging a Mixture-of-Experts (MoE) architecture, these models deliver industry-leading performance in understanding text and images. Marking the beginning of a new era for the Llama ecosystem, the series introduces two efficient models: Llama 4 Scout, a 17-billion-parameter model with 16 experts, and Llama 4 Maverick, also with 17 billion parameters but featuring 128 experts. Built as auto-regressive language models, the Llama 4 series incorporates early fusion to achieve seamless and native multimodality.",
        # Qwen
        ## https://huggingface.co/Qwen/Qwen3-0.6B
        "Qwen3-0.6B": "Qwen3-0.6B is a compact causal language model with 0.6B parameters, offering dense and MoE variants, improved reasoning, seamless mode switching, strong alignment, agent capabilities, multilingual support, and 32K context length.",
        ## https://huggingface.co/Qwen/Qwen3-1.7B
        "Qwen3-1.7B": "Qwen3-1.7B is a next-generation causal language model with 1.7B parameters, offering dense and MoE variants, enhanced reasoning, seamless mode switching, strong alignment, agent capabilities, multilingual support, and long-context processing up to 32K tokens.",
        ## https://huggingface.co/Qwen/Qwen3-4B
        "Qwen3-4B": "Qwen3 is the latest generation of large language models, featuring both dense and MoE variants with enhanced reasoning, instruction-following, agent capabilities, and multilingual support, including seamless mode switching, superior alignment, and long-context processing up to 131K tokens.",
        ## https://huggingface.co/Qwen/Qwen3-8B
        "Qwen3-8B": "Qwen3-8B is an advanced causal language model with 8.2B parameters, featuring dense and MoE variants, enhanced reasoning, seamless mode switching, strong alignment, agent capabilities, multilingual support, and long-context processing up to 131K tokens.",
        ## https://huggingface.co/Qwen/Qwen3-14B
        "Qwen3-14B": "Qwen3-14B is a large-scale causal language model with 14.8B parameters, offering dense and MoE variants, advanced reasoning, seamless mode switching, strong alignment, agent capabilities, multilingual support, and extended context handling up to 131K tokens.",
        ## https://huggingface.co/Qwen/Qwen3-32B
        "Qwen3-32B": "Qwen3-32B is a powerful causal language model with 32.8B parameters, featuring dense and MoE variants, enhanced reasoning, seamless mode switching, strong alignment, advanced agent capabilities, multilingual support, and long-context processing up to 131K tokens.",
        # Deepseek
        # https://huggingface.co/deepseek-ai/DeepSeek-V3
        "DeepSeek-v3": "DeepSeek-V3 is a 671B-parameter MoE language model (37B active per token) featuring MLA and DeepSeekMoE architectures, auxiliary-loss-free load balancing, and multi-token prediction, trained on 14.8T tokens with efficient GPU usage, achieving performance comparable to top closed-source models while maintaining stable training.",
        # https://huggingface.co/deepseek-ai/DeepSeek-V3.1
        "DeepSeek-V3.1": "DeepSeek-V3.1 extends DeepSeek-V3 with larger long-context training (630B tokens at 32K and 209B tokens at 128K) and adopts FP8 data formats for efficiency and compatibility.",
        # https://huggingface.co/deepseek-ai/DeepSeek-V3.2-Exp
        "DeepSeek-V3.2-Exp": "DeepSeek-V3.2-Exp, built on V3.1-Terminus, introduces Sparse Attention to improve training and inference efficiency for long-context processing as part of ongoing research into more efficient transformer architectures.",
        # Mistral
        # "Mistral" : "",
        # "Mixtral-8x7B": "",
        # gpt-oss
        # https://huggingface.co/openai/gpt-oss-20b
        "gpt-oss-20b": "The gpt-oss series, introduced by OpenAI, consists of open-weight models designed to support powerful reasoning, agentic tasks, and a wide range of developer use cases. Two versions are being released: gpt-oss-120b, a 117-billion-parameter model with 5.1 billion active parameters optimized for production-level, general-purpose, high-reasoning tasks that can fit into a single 80GB GPU such as the NVIDIA H100 or AMD MI300X; and gpt-oss-20b, a 21-billion-parameter model with 3.6 billion active parameters intended for lower latency, as well as local or specialized applications. Both models were trained using OpenAI’s harmony response format and must be used with this format to function correctly.",
        # Genma
        # https://huggingface.co/google/gemma-3-1b-it
        "gemma-3-1b-it": "Gemma is a family of lightweight open models from Google, built on the same research as Gemini. The latest Gemma 3 models are multimodal, supporting both text and image inputs with text generation outputs. They feature a 128K context window (32K for the 1B model), multilingual support in over 140 languages, and come in multiple sizes, making them suitable for tasks such as question answering, summarization, reasoning, and image understanding. Their smaller size allows deployment on laptops, desktops, or personal cloud infrastructure, broadening access to advanced AI. Inputs include text and images normalized to 896×896 resolution, while outputs are generated text with up to 8192 tokens of context.",
        # https://huggingface.co/google/gemma-3-4b-it
        "gemma-3-4b-it": "Gemma is a family of lightweight open models from Google, built on the same research behind the Gemini models. The latest Gemma 3 models are multimodal, capable of processing both text and images as input and generating text as output, with open weights for pre-trained and instruction-tuned variants. They offer a 128K context window (32K for the 1B model), support over 140 languages, and come in more sizes than earlier versions, making them suitable for tasks like question answering, summarization, reasoning, and image understanding. Thanks to their smaller size, Gemma models can run on laptops, desktops, or personal cloud setups, expanding access to advanced AI. Inputs include text and images (normalized to 896×896 and encoded to 256 tokens each), while outputs are generated text with up to 8192 tokens.",
        # https://huggingface.co/google/gemma-3-27b-it
        "gemma-3-27b-it": "Gemma is a family of lightweight open models from Google, built on the same research as the Gemini models. The Gemma 3 series is multimodal, able to take both text and image inputs and generate text outputs, with open weights available for both pre-trained and instruction-tuned versions. They feature a 128K context window (32K for the 1B model), multilingual support in more than 140 languages, and come in a wider range of sizes than previous releases. Well-suited for tasks such as question answering, summarization, reasoning, and image understanding, Gemma models are compact enough to run on laptops, desktops, or personal cloud setups, making advanced AI more broadly accessible. Inputs include text strings or images normalized to 896×896 and encoded into 256 tokens each, while outputs are generated text of up to 8192 tokens.",
        # BERT
    },
    "Vision Language Models": {},
    "Vision Language Action Models": {},
    "Diffusion Models": {},
}
