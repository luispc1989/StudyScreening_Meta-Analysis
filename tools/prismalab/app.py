from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pdf_fetcher.core.config import ACTIVE_PROJECT_ROOT, PROJECTS_ROOT_DIR, TOOLKIT_ROOT_DIR


APP_TITLE = "PrismaLab"
APP_SUBTITLE = "Project Workspace"


def set_page() -> None:
    st.set_page_config(
        page_title=f"{APP_TITLE} - {APP_SUBTITLE}",
        page_icon="ST",
        layout="wide",
    )


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --hub-panel-bg: linear-gradient(180deg, rgba(237, 244, 252, 0.92), rgba(248, 250, 253, 0.98));
            --hub-panel-border: rgba(79, 110, 145, 0.18);
            --hub-panel-shadow: 0 14px 34px rgba(60, 82, 110, 0.08);
            --hub-accent: #6cbcff;
            --hub-text-soft: #6a7483;
            --hub-badge-neutral-bg: rgba(100, 116, 139, 0.11);
            --hub-badge-neutral-text: #334155;
            --hub-badge-ok-bg: rgba(34, 197, 94, 0.14);
            --hub-badge-ok-text: #166534;
            --hub-badge-warn-bg: rgba(245, 158, 11, 0.16);
            --hub-badge-warn-text: #9a6700;
            --hub-badge-danger-bg: rgba(239, 68, 68, 0.14);
            --hub-badge-danger-text: #b42318;
        }

        .block-container {
            padding-top: 1.15rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(120, 130, 150, 0.14);
        }

        .hub-hero {
            padding: 1.15rem 1.2rem 1.15rem 1.2rem;
            border: 1px solid var(--hub-panel-border);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(111, 194, 255, 0.16), rgba(255, 255, 255, 0.96));
            box-shadow: var(--hub-panel-shadow);
            margin-bottom: 1rem;
        }

        .hub-title {
            margin: 0;
            font-size: clamp(2rem, 2.8vw, 3rem);
            font-weight: 850;
            line-height: 1.02;
            letter-spacing: -0.03em;
            color: #24324a;
        }

        .hub-subtitle {
            margin: 0.35rem 0 0 0;
            font-size: 1rem;
            color: var(--hub-text-soft);
            line-height: 1.45;
            max-width: 68rem;
        }

        .hub-panel {
            padding: 1rem 1.05rem 1.05rem 1.05rem;
            border: 1px solid var(--hub-panel-border);
            border-radius: 20px;
            background: var(--hub-panel-bg);
            box-shadow: var(--hub-panel-shadow);
            margin-bottom: 1rem;
        }

        .hub-panel-title {
            margin: 0 0 0.9rem 0;
            font-size: 1rem;
            font-weight: 800;
            color: var(--hub-accent);
            padding-bottom: 0.55rem;
            border-bottom: 1px solid rgba(120, 130, 150, 0.22);
        }

        .hub-kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 1rem;
        }

        .hub-kpi {
            padding: 0.85rem 0.95rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.68);
            border: 1px solid rgba(120, 130, 150, 0.16);
        }

        .hub-kpi-label {
            font-size: 0.95rem;
            color: var(--hub-text-soft);
            font-weight: 700;
            margin-bottom: 0.55rem;
        }

        .hub-kpi-value {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 3rem;
            padding: 0.25rem 0.7rem;
            border-radius: 0.75rem;
            background: rgba(120, 130, 150, 0.1);
            color: #24324a;
            font-size: 1.9rem;
            font-weight: 850;
            line-height: 1;
        }

        .hub-tool-card {
            padding: 1rem;
            border-radius: 20px;
            border: 1px solid rgba(120, 130, 150, 0.16);
            background: rgba(255, 255, 255, 0.72);
            min-height: 12.25rem;
        }

        .hub-tool-name {
            margin: 0 0 0.3rem 0;
            font-size: 1.25rem;
            font-weight: 850;
            color: #24324a;
        }

        .hub-tool-desc {
            margin: 0 0 0.85rem 0;
            color: var(--hub-text-soft);
            line-height: 1.45;
            font-size: 0.96rem;
        }

        .hub-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            padding: 0.32rem 0.72rem;
            font-size: 0.82rem;
            font-weight: 800;
            line-height: 1;
            white-space: nowrap;
        }

        .hub-badge.neutral { background: var(--hub-badge-neutral-bg); color: var(--hub-badge-neutral-text); }
        .hub-badge.ok { background: var(--hub-badge-ok-bg); color: var(--hub-badge-ok-text); }
        .hub-badge.warn { background: var(--hub-badge-warn-bg); color: var(--hub-badge-warn-text); }
        .hub-badge.danger { background: var(--hub-badge-danger-bg); color: var(--hub-badge-danger-text); }

        .hub-list {
            display: grid;
            gap: 0.7rem;
        }

        .hub-list-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: center;
            gap: 0.85rem;
            padding: 0.1rem 0;
        }

        .hub-list-label {
            color: #24324a;
            font-size: 0.98rem;
            font-weight: 700;
        }

        .hub-list-value {
            color: var(--hub-text-soft);
            font-size: 0.96rem;
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def list_projects() -> list[Path]:
    if not PROJECTS_ROOT_DIR.exists():
        return []
    return sorted([path for path in PROJECTS_ROOT_DIR.iterdir() if path.is_dir()], key=lambda p: p.name.lower())


def init_state() -> None:
    projects = list_projects()
    default_project = ACTIVE_PROJECT_ROOT.name if ACTIVE_PROJECT_ROOT.exists() else (projects[0].name if projects else "No project")
    st.session_state.setdefault("hub_selected_project", default_project)
    st.session_state.setdefault("hub_page", "Dashboard")


def render_sidebar() -> None:
    projects = list_projects()
    project_names = [path.name for path in projects] or ["No project found"]

    with st.sidebar:
        st.markdown("## PrismaLab")
        st.caption("Project workspace prototype")
        st.selectbox(
            "Active project",
            project_names,
            key="hub_selected_project",
            help="This prototype only changes the visible project context.",
        )
        st.radio(
            "Navigate",
            ["Dashboard", "Projects", "Tools", "Architecture", "Settings"],
            key="hub_page",
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.caption(f"Toolkit root: `{TOOLKIT_ROOT_DIR}`")


def render_hero() -> None:
    st.markdown(
        f"""
        <div class="hub-hero">
            <h1 class="hub-title">{APP_TITLE}</h1>
            <p class="hub-subtitle">
                A central workspace to manage projects, open tools, track progress across the meta-analysis workflow,
                and later coordinate a shared local database for long-term project continuity.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    st.markdown('<div class="hub-panel-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hub-kpi-grid">
            <div class="hub-kpi">
                <div class="hub-kpi-label">Projects</div>
                <div class="hub-kpi-value">1</div>
            </div>
            <div class="hub-kpi">
                <div class="hub-kpi-label">Active tools</div>
                <div class="hub-kpi-value">1</div>
            </div>
            <div class="hub-kpi">
                <div class="hub-kpi-label">Phase states</div>
                <div class="hub-kpi-value">3</div>
            </div>
            <div class="hub-kpi">
                <div class="hub-kpi-label">Next milestone</div>
                <div class="hub-kpi-value">DB</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([1.45, 1.0], vertical_alignment="top")
    with col_a:
        st.markdown('<div class="hub-panel">', unsafe_allow_html=True)
        st.markdown('<div class="hub-panel-title">Continue Where You Left Off</div>', unsafe_allow_html=True)
        tool_cards = [
            (
                "PDF Fetcher",
                "DOI enrichment, PDF acquisition, Sci-Hub fallback, and S.C.O.U.T. manual review.",
                "Active prototype",
                "ok",
            ),
            (
                "Study Screening",
                "Planned integration for title/abstract and full-text screening workflow.",
                "Planned",
                "neutral",
            ),
            (
                "Meta-analysis",
                "Planned analysis workspace for outcomes, effect sizes, and reporting outputs.",
                "Planned",
                "neutral",
            ),
        ]
        cols = st.columns(3, vertical_alignment="top")
        for col, (name, desc, badge, badge_class) in zip(cols, tool_cards):
            with col:
                st.markdown(
                    f"""
                    <div class="hub-tool-card">
                        <div class="hub-tool-name">{name}</div>
                        <div class="hub-tool-desc">{desc}</div>
                        <div class="hub-badge {badge_class}">{badge}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="hub-panel">', unsafe_allow_html=True)
        st.markdown('<div class="hub-panel-title">Project Snapshot</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="hub-list">
                <div class="hub-list-row">
                    <div class="hub-list-label">Selected project</div>
                    <div class="hub-list-value">{st.session_state['hub_selected_project']}</div>
                </div>
                <div class="hub-list-row">
                    <div class="hub-list-label">Project root</div>
                    <div class="hub-list-value">{ACTIVE_PROJECT_ROOT}</div>
                </div>
                <div class="hub-list-row">
                    <div class="hub-list-label">Data engine</div>
                    <div class="hub-list-value">Planned SQLite project database</div>
                </div>
                <div class="hub-list-row">
                    <div class="hub-list-label">Current status</div>
                    <div class="hub-list-value">Foundation design phase</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


def render_projects() -> None:
    projects = list_projects()
    st.markdown('<div class="hub-panel">', unsafe_allow_html=True)
    st.markdown('<div class="hub-panel-title">Projects</div>', unsafe_allow_html=True)
    if not projects:
        st.info("No local projects were found yet.")
    else:
        for project_path in projects:
            col_info, col_status = st.columns([5, 1.2], vertical_alignment="center")
            with col_info:
                st.markdown(f"**{project_path.name}**")
                st.caption(str(project_path))
            with col_status:
                badge = "Active" if project_path.name == st.session_state["hub_selected_project"] else "Available"
                badge_class = "ok" if badge == "Active" else "neutral"
                st.markdown(f'<div class="hub-badge {badge_class}">{badge}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="hub-panel">', unsafe_allow_html=True)
    st.markdown('<div class="hub-panel-title">Why This Is Not a Technical Menu</div>', unsafe_allow_html=True)
    st.write(
        "A technical menu usually feels like a list of scripts, flags, and internal operations. "
        "This prototype is instead organized around projects, workflow areas, and next actions, "
        "so the interface reads like a workbench rather than a command launcher."
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_tools() -> None:
    cols = st.columns(3, vertical_alignment="top")
    cards = [
        ("PDF Fetcher", "The current active tool. Will later plug into the shared project database.", "Ready to integrate", "ok"),
        ("Literature Search", "Future tool for loading and updating search results across years and databases.", "Planned", "neutral"),
        ("Data Extraction", "Future structured extraction workspace for outcomes, populations, interventions, and effect data.", "Planned", "neutral"),
    ]
    for col, (title, desc, badge, badge_class) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="hub-tool-card">
                    <div class="hub-tool-name">{title}</div>
                    <div class="hub-tool-desc">{desc}</div>
                    <div class="hub-badge {badge_class}">{badge}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_architecture() -> None:
    st.markdown('<div class="hub-panel">', unsafe_allow_html=True)
    st.markdown('<div class="hub-panel-title">Architecture Direction</div>', unsafe_allow_html=True)
    st.write(
        "The intended architecture is: Excel import -> local SQLite project database -> tool workflows "
        "-> optional Excel export. This enables long-term project continuity, project sharing, and future "
        "incremental updates when a meta-analysis is repeated years later."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="hub-panel">', unsafe_allow_html=True)
    st.markdown('<div class="hub-panel-title">Planned Foundation Steps</div>', unsafe_allow_html=True)
    st.markdown(
        """
        1. Create the project database file per project.
        2. Import workbook records into the database.
        3. Expose project and tool state in the hub.
        4. Migrate PDF Fetcher phases progressively to database-backed execution.
        """.strip()
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_settings() -> None:
    st.markdown('<div class="hub-panel">', unsafe_allow_html=True)
    st.markdown('<div class="hub-panel-title">Settings Preview</div>', unsafe_allow_html=True)
    st.write(
        "This is where future project-wide settings would live: email provider configuration, "
        "local paths, API integration toggles, browser preferences, and tool-level defaults."
    )
    st.markdown(
        """
        - Email API settings
        - Project database path
        - PDF download directory
        - Browser automation preferences
        - Tool visibility in the hub
        """.strip()
    )
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    set_page()
    inject_css()
    init_state()
    render_sidebar()
    render_hero()

    page = st.session_state["hub_page"]
    if page == "Dashboard":
        render_dashboard()
    elif page == "Projects":
        render_projects()
    elif page == "Tools":
        render_tools()
    elif page == "Architecture":
        render_architecture()
    else:
        render_settings()


if __name__ == "__main__":
    main()
