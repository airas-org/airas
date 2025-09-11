from airas.types.research_study import ResearchStudy

create_method_subgraph_v2_input_data = {
    "research_topic": "Deep Learning for Natural Language Processing",
    "research_study_list": [
        ResearchStudy(
            title="Attention is All You Need",
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
        ),
        ResearchStudy(
            title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            abstract="We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
        ),
        ResearchStudy(
            title="Language Models are Few-Shot Learners",
            abstract="Recent work has demonstrated substantial gains on many NLP tasks and benchmarks by pre-training on a large corpus of text followed by fine-tuning on a specific task. While typically task-agnostic in architecture, this method still requires task-specific fine-tuning datasets of thousands or tens of thousands of examples.",
        ),
    ],
}
