# Time Series libraries: documentation endpoints
# served via the get_library_docs MCP tool. Verify every URL is
# reachable (curl) before adding an entry; the weekly link-check
# workflow guards against rot afterwards.
TIME_SERIES_LIBRARIES: dict[str, dict[str, str | None]] = {
    "darts": {
        "description": "Unified forecasting library (classical to deep models)",
        "category": "time_series",
        "official_docs": "https://unit8co.github.io/darts",
        "github": "https://github.com/unit8co/darts",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "sktime": {
        "description": "scikit-learn-compatible time series learning framework",
        "category": "time_series",
        "official_docs": "https://www.sktime.net",
        "github": "https://github.com/sktime/sktime",
        "llms_txt": "https://www.sktime.net/llms.txt",
        "llms_full_txt": None,
    },
    "statsforecast": {
        "description": "Fast classical forecasting (ARIMA, ETS) at scale",
        "category": "time_series",
        "official_docs": "https://nixtlaverse.nixtla.io/statsforecast",
        "github": "https://github.com/Nixtla/statsforecast",
        "llms_txt": "https://nixtlaverse.nixtla.io/llms.txt",
        "llms_full_txt": "https://nixtlaverse.nixtla.io/llms-full.txt",
    },
    "neuralforecast": {
        "description": "Deep learning forecasting models (NBEATS, NHITS, TFT)",
        "category": "time_series",
        "official_docs": "https://nixtlaverse.nixtla.io/neuralforecast",
        "github": "https://github.com/Nixtla/neuralforecast",
        "llms_txt": "https://nixtlaverse.nixtla.io/llms.txt",
        "llms_full_txt": "https://nixtlaverse.nixtla.io/llms-full.txt",
    },
    "gluonts": {
        "description": "Probabilistic time series modeling",
        "category": "time_series",
        "official_docs": "https://ts.gluon.ai",
        "github": "https://github.com/awslabs/gluonts",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
