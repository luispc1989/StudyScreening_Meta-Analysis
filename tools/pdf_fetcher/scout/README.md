# S.C.O.U.T.

S.C.O.U.T. is a semi-assisted review sub-tool inside `tools/pdf_fetcher`.

It is responsible for:

- loading failed-case Excel reports;
- opening article links case by case;
- tracking likely PDF downloads;
- saving structured manual review decisions.

## Entry points

- Streamlit app: `tools/pdf_fetcher/scout/app.py`
- Browser helper: `tools/pdf_fetcher/scout/browser.py`
- Launcher: `tools/pdf_fetcher/run_scout.bat`

## Related folders

- browser extension: `tools/pdf_fetcher/browser_extension/scout_download_bridge/`
- local browser runtime data: `tools/pdf_fetcher/browser_profiles/`

`browser_profiles/` is local runtime state and should stay out of version control.
