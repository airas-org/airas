from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_iteration import ResearchIteration
from airas.types.research_session import ResearchSession
from airas.types.research_study import LLMExtractedInfo, MetaData, ResearchStudy

create_bibfile_subgraph_input_data = {
    "research_study_list": [
        ResearchStudy(
            title="Deep Learning for Natural Language Processing: A Comprehensive Survey",
            abstract="This paper presents a comprehensive survey of deep learning techniques applied to natural language processing tasks, including sentiment analysis, machine translation, and text classification.",
            meta_data=MetaData(
                authors=["Smith, John", "Johnson, Alice"],
                published_date="2023-01-01",
                venue="Nature Machine Intelligence",
                volume="5",
                issue="3",
                pages="123-145",
                doi="10.1038/s42256-023-00567-8",
                pdf_url="https://arxiv.org/abs/2301.12345",
                github_url="https://github.com/nlp-survey/deep-learning-nlp",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Comprehensive survey of deep learning techniques for NLP",
                methodology="Literature review and comparative analysis",
                experimental_setup="Analysis of multiple NLP benchmarks",
                limitations="Survey scope limited to English language tasks",
                future_research_directions="Multimodal and multilingual applications",
            ),
        ),
        ResearchStudy(
            title="Transformer Networks: Architecture and Applications",
            abstract="We explore the transformer architecture and its applications across various domains including computer vision and natural language processing.",
            meta_data=MetaData(
                authors=["Brown, Michael", "Davis, Sarah"],
                published_date="2024-01-01",
                venue="Journal of Machine Learning Research",
                volume="25",
                pages="1-28",
                doi="10.5555/3648699.3648700",
                pdf_url="https://arxiv.org/abs/2401.56789",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Transformer architecture analysis and cross-domain applications",
                methodology="Architecture analysis and empirical evaluation",
                experimental_setup="Computer vision and NLP benchmarks",
                limitations="Limited to specific transformer variants",
                future_research_directions="Efficiency improvements and novel architectures",
            ),
        ),
    ],
    "reference_research_study_list": [
        ResearchStudy(
            title="Attention Is All You Need",
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism.",
            meta_data=MetaData(
                authors=["Vaswani, Ashish", "Shazeer, Noam", "Parmar, Niki"],
                published_date="2017-06-12",
                venue="Advances in Neural Information Processing Systems",
                volume="30",
                doi="10.48550/arXiv.1706.03762",
                pdf_url="https://arxiv.org/abs/1706.03762",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Introduced the Transformer architecture based solely on attention mechanisms",
                methodology="Multi-head self-attention mechanism with positional encoding",
                experimental_setup="Machine translation tasks on WMT datasets",
                limitations="Requires large amounts of training data",
                future_research_directions="Applications to other modalities and efficiency improvements",
            ),
        ),
        ResearchStudy(
            title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            abstract="We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers.",
            meta_data=MetaData(
                authors=["Devlin, Jacob", "Chang, Ming-Wei", "Lee, Kenton"],
                published_date="2018-10-11",
                venue="Proceedings of NAACL-HLT",
                pages="4171-4186",
                doi="10.18653/v1/N19-1423",
                pdf_url="https://arxiv.org/abs/1810.04805",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Bidirectional transformer pre-training for language understanding",
                methodology="Masked language modeling and next sentence prediction",
                experimental_setup="GLUE benchmark and various NLP tasks",
                limitations="Computational requirements and fixed input length",
                future_research_directions="Larger models and task-specific adaptations",
            ),
        ),
        ResearchStudy(
            title="GPT-3: Language Models are Few-Shot Learners",
            abstract="Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task.",
            meta_data=MetaData(
                authors=["Brown, Tom B.", "Mann, Benjamin", "Ryder, Nick"],
                published_date="2020-05-28",
                venue="Advances in Neural Information Processing Systems",
                volume="33",
                pages="1877-1901",
                pdf_url="https://arxiv.org/abs/2005.14165",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Large-scale autoregressive language model with few-shot learning capabilities",
                methodology="Autoregressive language modeling at scale",
                experimental_setup="Various NLP benchmarks with few-shot prompting",
                limitations="Computational cost and potential biases",
                future_research_directions="More efficient training and alignment techniques",
            ),
        ),
        ResearchStudy(
            title="Computer Vision and Pattern Recognition Methods",
            abstract="This paper focuses on traditional computer vision techniques for image classification and object detection without deep learning approaches.",
            meta_data=MetaData(
                authors=["Wilson, Robert", "Taylor, Emma"],
                published_date="2019-03-15",
                venue="Computer Vision Research",
                volume="12",
                issue="4",
                pages="88-102",
                doi="10.1234/cvr.2019.12345",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Traditional computer vision methods for classification and detection",
                methodology="Feature extraction and classical machine learning approaches",
                experimental_setup="Standard computer vision datasets",
                limitations="Performance limitations compared to deep learning",
                future_research_directions="Hybrid approaches combining traditional and deep methods",
            ),
        ),
        ResearchStudy(
            title="ResNet: Deep Residual Learning for Image Recognition",
            abstract="Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously.",
            meta_data=MetaData(
                authors=["He, Kaiming", "Zhang, Xiangyu", "Ren, Shaoqing"],
                published_date="2016-12-10",
                venue="Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition",
                pages="770-778",
                doi="10.1109/CVPR.2016.90",
                pdf_url="https://arxiv.org/abs/1512.03385",
            ),
            llm_extracted_info=LLMExtractedInfo(
                main_contributions="Residual learning framework for training very deep networks",
                methodology="Skip connections and residual blocks",
                experimental_setup="ImageNet classification and object detection",
                limitations="Memory requirements for very deep networks",
                future_research_directions="More efficient architectures and training methods",
            ),
        ),
    ],
    "research_session": ResearchSession(
        hypothesis=ResearchHypothesis(
            open_problems="Diffusion models suffer from slow sampling speed",
            method="Improve existing method with adaptive step sizes",
            experimental_setup="Test on CIFAR-10 and ImageNet datasets",
            experimental_code="Using PyTorch and diffusers library",
            expected_result="Achieve even better convergence",
            expected_conclusion="Further acceleration",
        ),
        iterations=[
            ResearchIteration(
                method="Propose a novel training-free acceleration method using higher-order approximation",
            )
        ],
    ),
    "github_repository_info": GitHubRepositoryInfo(
        github_owner="auto-res2",
        repository_name="airas-20251009-055033-matsuzawa",
        branch_name="main",
    ),
}
