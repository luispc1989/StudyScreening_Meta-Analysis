from pathlib import Path

"""Wiley resolver prototype target."""

PUBLISHER = "Wiley"
ARTICLE_URL = "https://doi.org/10.1111/j.1439-0523.2007.01460.x"
SOURCE_URL = "https://onlinelibrary.wiley.com/doi/10.1111/j.1439-0523.2007.01460.x"
DOI = "10.1111/j.1439-0523.2007.01460.x"
RECORD_ID = "19"
TITLE = "Reduction in kernel weight as a potential indirect selection criterion for wheat grain yield under terminal heat stress"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "wiley"


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
