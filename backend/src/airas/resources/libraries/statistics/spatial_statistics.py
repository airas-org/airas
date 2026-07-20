# statistics / spatial_statistics documentation endpoints (shared domain>category
# taxonomy across resources/{libraries,models,datasets}). Verify
# every URL (curl) before adding an entry; the weekly link-check
# workflow guards against rot.
SPATIAL_STATISTICS_LIBRARIES: dict[str, dict[str, str | None]] = {
    "geopandas": {
        "description": "Geographic data structures and operations on GeoDataFrames",
        "domain": "statistics",
        "category": "spatial_statistics",
        "official_docs": "https://geopandas.org/en/stable",
        "github": "https://github.com/geopandas/geopandas",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "pysal": {
        "description": "Spatial analysis library (autocorrelation, econometrics)",
        "domain": "statistics",
        "category": "spatial_statistics",
        "official_docs": "https://pysal.org/pysal",
        "github": "https://github.com/pysal/pysal",
        "llms_txt": None,
        "llms_full_txt": None,
    },
    "shapely": {
        "description": "Manipulation and analysis of planar geometric objects",
        "domain": "statistics",
        "category": "spatial_statistics",
        "official_docs": "https://shapely.readthedocs.io/en/stable",
        "github": "https://github.com/shapely/shapely",
        "llms_txt": None,
        "llms_full_txt": None,
    },
}
