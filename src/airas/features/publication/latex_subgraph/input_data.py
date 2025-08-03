latex_subgraph_input_data = {
    "github_repository": {
        "github_owner": "auto-res2",
        "repository_name": "tanaka-20250804",
        "branch_name": "main",
    },
    "paper_content": {
        "Title": "Advanced Neural Network Architectures for Multi-Modal Learning",
        "Abstract": "This paper presents a novel approach to multi-modal learning that combines transformer architectures with convolutional neural networks. Our method achieves state-of-the-art performance on several benchmark datasets including ImageNet and COCO. We demonstrate significant improvements in both accuracy and computational efficiency compared to existing approaches. The proposed architecture shows particular strength in handling heterogeneous data types and can be applied to various computer vision and natural language processing tasks.",
        "Introduction": "Multi-modal learning has become increasingly important in modern machine learning applications. Traditional approaches often struggle with integrating information from different modalities effectively [john_2023_deep]. Recent advances in transformer architectures have shown promising results in handling sequential data [ashish_2017_attention], while convolutional networks remain the gold standard for image processing tasks. Our work bridges these approaches by proposing a unified architecture that can process both visual and textual information simultaneously.",
        "Related_Work": "Previous work in multi-modal learning can be categorized into several approaches. Early fusion methods combine features at the input level, while late fusion approaches merge predictions from individual modality-specific models. [michael_2024_transformer] demonstrated the effectiveness of transformer architectures across various domains. [b_2020_gpt] showed that large-scale pre-training can significantly improve performance on downstream tasks. However, these approaches often fail to capture complex cross-modal interactions that are crucial for many real-world applications.",
        "Method": "Our proposed architecture consists of three main components: (1) a visual encoder based on ResNet-50, (2) a textual encoder using BERT-base, and (3) a cross-modal fusion module implemented using multi-head attention. The fusion module allows for dynamic weighting of features from different modalities based on the input context. We employ a joint training strategy that optimizes both modality-specific and cross-modal objectives simultaneously.",
        "Experiments": "We evaluate our approach on three benchmark datasets: VQA 2.0, MSCOCO Caption, and Flickr30K. Our method achieves 72.4% accuracy on VQA 2.0, surpassing the previous best result by 3.2%. On MSCOCO Caption, we obtain a BLEU-4 score of 38.6, which represents a 2.1% improvement over the baseline. Training was performed using Adam optimizer with a learning rate of 1e-4 and batch size of 32.",
        "Results": "Figure 1 shows the convergence behavior of our model during training. The proposed method converges faster and achieves lower final loss compared to baseline approaches. Figure 2 illustrates the attention weights learned by the cross-modal fusion module, demonstrating that the model learns to focus on relevant visual regions when processing textual queries. Performance comparisons across different datasets are presented in Figure 3, showing consistent improvements over existing methods.",
        "Conclusion": "We have presented a novel multi-modal learning architecture that effectively combines visual and textual information processing. Our experimental results demonstrate significant improvements over existing approaches across multiple benchmark datasets. The proposed cross-modal fusion mechanism shows promise for various applications including visual question answering, image captioning, and multimodal retrieval. Future work will explore extension to additional modalities such as audio and video data.",
    },
    "references_bib": """% ===========================================
% REQUIRED CITATIONS
% These papers must be cited in the manuscript
% ===========================================

@article{john_2023_deep,
 abstract = {This paper presents a comprehensive survey of deep learning techniques applied to natural language processing tasks, including sentiment analysis, machine translation, and text classification.},
 arxiv_url = {https://arxiv.org/abs/2301.12345},
 author = {Smith, John and Johnson, Alice},
 doi = {10.1038/s42256-023-00567-8},
 github_url = {https://github.com/nlp-survey/deep-learning-nlp},
 journal = {Nature Machine Intelligence},
 number = {3},
 pages = {123-145},
 title = {Deep Learning for Natural Language Processing: A Comprehensive Survey},
 volume = {5},
 year = {2023}
}

@article{michael_2024_transformer,
 abstract = {We explore the transformer architecture and its applications across various domains including computer vision and natural language processing.},
 arxiv_url = {https://arxiv.org/abs/2401.56789},
 author = {Brown, Michael and Davis, Sarah},
 doi = {10.5555/3648699.3648700},
 journal = {Journal of Machine Learning Research},
 pages = {1-28},
 title = {Transformer Networks: Architecture and Applications},
 volume = {25},
 year = {2024}
}

% ===========================================
% REFERENCE CANDIDATES
% Additional reference papers for context
% ===========================================

@article{ashish_2017_attention,
 abstract = {The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism.},
 arxiv_url = {https://arxiv.org/abs/1706.03762},
 author = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki},
 doi = {10.48550/arXiv.1706.03762},
 journal = {Advances in Neural Information Processing Systems},
 title = {Attention Is All You Need},
 volume = {30},
 year = {2017}
}

@article{b_2020_gpt,
 abstract = {Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task.},
 arxiv_url = {https://arxiv.org/abs/2005.14165},
 author = {Brown, Tom B. and Mann, Benjamin and Ryder, Nick},
 journal = {Advances in Neural Information Processing Systems},
 pages = {1877-1901},
 title = {GPT-3: Language Models are Few-Shot Learners},
 volume = {33},
 year = {2020}
}""",
    "image_file_name_list": ["figure1.png", "figure2.jpg"],
}
