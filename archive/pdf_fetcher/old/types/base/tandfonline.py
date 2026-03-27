from pathlib import Path

"""Taylor & Francis resolver prototype target."""

PUBLISHER = "Taylor & Francis"
ARTICLE_URL = "https://doi.org/10.1080/03650340.2022.2130265"
SOURCE_URL = "https://www.tandfonline.com/doi/full/10.1080/03650340.2022.2130265"
DOI = "10.1080/03650340.2022.2130265"
RECORD_ID = "128"
TITLE = "24-Epicastasterone and KH2PO4 protect grain production of wheat crops from terminal heat impacts by modulating leaf physiology"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "tandfonline"


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
