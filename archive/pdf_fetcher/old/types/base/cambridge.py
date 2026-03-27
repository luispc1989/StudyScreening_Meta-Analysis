from pathlib import Path

"""Cambridge resolver prototype target."""

PUBLISHER = "Cambridge"
ARTICLE_URL = "https://doi.org/10.1017/s002185961900087x"
SOURCE_URL = "https://www.cambridge.org/core/journals/journal-of-agricultural-science/article/abs/efficacy-of-calcium-chloride-and-arginine-foliar-spray-in-alleviating-terminal-heat-stress-in-latesown-wheat-triticum-aestivum-l/84DF205D14E6C890AF1628AB20005F85"
DOI = "10.1017/s002185961900087x"
RECORD_ID = "288"
TITLE = "Efficacy of calcium chloride and arginine foliar spray in alleviating terminal heat stress in late-sown wheat (Triticum aestivum L.)"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "cambridge"


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
