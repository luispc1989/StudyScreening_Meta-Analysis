from pathlib import Path

"""Nature resolver prototype target."""

PUBLISHER = "Nature"
ARTICLE_URL = "https://doi.org/10.1038/s41598-025-89144-4"
SOURCE_URL = "https://www.nature.com/articles/s41598-025-89144-4.pdf"
DOI = "10.1038/s41598-025-89144-4"
RECORD_ID = "333"
TITLE = "Enriched grain minerals in Aegilops tauschii-derived common wheat population under heat-stress environments"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "nature"


def sample_case() -> dict[str, str]:
    return {
        "publisher": PUBLISHER,
        "record_id": RECORD_ID,
        "doi": DOI,
        "article_url": ARTICLE_URL,
        "source_url": SOURCE_URL,
        "title": TITLE,
        "output_dir": str(OUTPUT_DIR),
    }


if __name__ == "__main__":
    for key, value in sample_case().items():
        print(f"{key}: {value}")
