from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import BrowserContext, Download, Error as PlaywrightError, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


REPO_ROOT = Path(__file__).resolve().parents[3]
PROFILE_ROOT = REPO_ROOT / "tools" / "pdf_fetcher" / "browser_profiles" / "scout"


def wait_for_page_ready(page: Page, timeout_ms: int = 30000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(1500)


def attach_download_handler(page: Page, expected_output: Path) -> None:
    def _handle_download(download: Download) -> None:
        expected_output.parent.mkdir(parents=True, exist_ok=True)
        download.save_as(str(expected_output))
        print(f"[S.C.O.U.T.] Download saved to: {expected_output}", flush=True)

    page.on("download", _handle_download)


def launch_persistent_browser(pw, user_data_dir: Path) -> tuple[BrowserContext, str]:
    launch_options = {
        "headless": False,
        "accept_downloads": True,
        "viewport": {"width": 1440, "height": 960},
        "locale": "en-US",
        "args": [
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
        ],
    }

    attempts: list[tuple[str | None, str]] = [
        ("chrome", "Google Chrome"),
        ("msedge", "Microsoft Edge"),
        (None, "Playwright Chromium"),
    ]

    last_error: Exception | None = None
    for channel, label in attempts:
        try:
            context = pw.chromium.launch_persistent_context(
                str(user_data_dir),
                channel=channel,
                **launch_options,
            )
            return context, label
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"Could not launch a persistent browser context: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch a dedicated S.C.O.U.T. browser window.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--label", default="Current case")
    args = parser.parse_args()

    url = args.url.strip()
    expected_output = Path(args.output).expanduser().resolve()
    label = args.label.strip() or "Current case"

    user_data_dir = PROFILE_ROOT
    user_data_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        context, browser_label = launch_persistent_browser(pw, user_data_dir)

        def _attach(page: Page) -> None:
            page.set_default_timeout(30000)
            attach_download_handler(page, expected_output)

        for existing_page in context.pages:
            _attach(existing_page)
        context.on("page", _attach)

        page = context.new_page()
        _attach(page)
        page.goto(url, wait_until="domcontentloaded")
        wait_for_page_ready(page, timeout_ms=5000)

        print(f"[S.C.O.U.T.] Browser opened for: {label}", flush=True)
        print(f"[S.C.O.U.T.] Browser engine: {browser_label}", flush=True)
        print(f"[S.C.O.U.T.] URL: {url}", flush=True)
        print(f"[S.C.O.U.T.] Expected output: {expected_output}", flush=True)
        print("[S.C.O.U.T.] No automatic challenge handling is active. Continue manually in this window.", flush=True)

        try:
            while True:
                if not any(not p.is_closed() for p in context.pages):
                    break
                page.wait_for_timeout(1000)
        finally:
            try:
                context.close()
            except PlaywrightError:
                pass


if __name__ == "__main__":
    main()
