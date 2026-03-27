from pathlib import Path

"""Oxford Academic resolver prototype target."""

PUBLISHER = "Oxford Academic"
ARTICLE_URL = "https://doi.org/10.1093/jxb/erab044"
SOURCE_URL = "https://academic.oup.com/jxb/article/72/10/3774/6128899"
DOI = "10.1093/jxb/erab044"
RECORD_ID = "105"
TITLE = "The wheat Seven in absentia gene is associated with increases in biomass and yield in hot climates"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "oxford"


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
