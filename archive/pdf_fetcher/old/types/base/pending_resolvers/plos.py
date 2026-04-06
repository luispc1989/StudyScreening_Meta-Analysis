from pathlib import Path

"""PLOS resolver prototype target."""

PUBLISHER = "PLOS"
ARTICLE_URL = "https://doi.org/10.1371/journal.pone.0126097"
SOURCE_URL = "https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0126097&type=printable"
DOI = "10.1371/journal.pone.0126097"
RECORD_ID = "1849"
TITLE = "Response of Spring Wheat (Triticum aestivum L.) Quality Traits and Yield to Sowing Date"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "plos"


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
