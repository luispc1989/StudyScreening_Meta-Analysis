from pathlib import Path

"""AKJournals resolver prototype target."""

PUBLISHER = "AKJournals"
ARTICLE_URL = "https://doi.org/10.1556/crc.38.2010.4.8"
SOURCE_URL = "https://akjournals.com/doi/abs/10.1556/CRC.38.2010.4.8"
DOI = "10.1556/crc.38.2010.4.8"
RECORD_ID = "48"
TITLE = "Grain Yield in Wheat as Affected by Short Periods of High Temperature, Drought and their Interaction during Pre- and Post-anthesis Stages"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "akjournals"


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
