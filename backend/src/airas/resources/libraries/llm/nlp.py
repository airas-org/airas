# Nlp (llm): documentation endpoints served via the
# get_library_docs MCP tool. Verify every URL (curl) before adding
# an entry; the weekly link-check workflow guards against rot.
NLP_LIBRARIES: dict[str, dict[str, str | None]] = {
    "spacy": {
        "description": "Industrial-strength NLP pipelines (NER, POS, dependency parsing)",
        "domain": "llm",
        "category": "nlp",
        "official_docs": "https://spacy.io/api",
        "github": "https://github.com/explosion/spaCy",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "nltk": {
        "description": "Classical NLP toolkit (tokenization, stemming, corpora)",
        "domain": "llm",
        "category": "nlp",
        "official_docs": "https://www.nltk.org",
        "github": "https://github.com/nltk/nltk",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "gensim": {
        "description": "Topic modeling and word embeddings (LDA, word2vec)",
        "domain": "llm",
        "category": "nlp",
        "official_docs": "https://radimrehurek.com/gensim/auto_examples",
        "github": "https://github.com/piskvorky/gensim",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
