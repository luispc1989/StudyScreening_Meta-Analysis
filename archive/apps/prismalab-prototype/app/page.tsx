'use client';

import { useState } from 'react';

/* ─── Phase data ──────────────────────────────────────────────────────── */

// Five spectrum rays → five phases of synthesis (brand guide §01)
// search=blue · screen=green · extract=amber · appraise=coral · analyse=violet
const PHASE_ACCENTS = [
  '#1C3558', // 1 Question definition — navy (foundation)
  '#378ADD', // 2 Literature search   — blue ray
  '#1D9E75', // 3 Study screening     — green ray (currently active)
  '#D85A30', // 4 Critical appraisal  — coral ray
  '#EF9F27', // 5 Data extraction     — amber ray
  '#7F77DD', // 6 Statistical synthesis — violet ray
  '#5DCAA5', // 7 Discussion          — teal (convergence)
];

const WORKFLOW_PHASES = [
  {
    name: 'Question definition',
    status: 'Planned',
    tone: 'neutral' as const,
    tools: ['Protocol Builder', 'Question Framing', 'Eligibility Design'],
    note: 'Define the review question, outcomes, and inclusion logic.',
  },
  {
    name: 'Literature search',
    status: 'Planned',
    tone: 'neutral' as const,
    tools: ['Search Importer', 'Database Connectors', 'Search Update Tracker'],
    note: 'Collect and structure database exports before screening starts.',
  },
  {
    name: 'Study screening',
    status: 'Active',
    tone: 'active' as const,
    tools: ['PDF Fetcher', 'Title/Abstract Screening', 'Full-text Screening'],
    note: 'This is the current live workflow area and the natural home of PDF retrieval.',
  },
  {
    name: 'Critical appraisal',
    status: 'Planned',
    tone: 'neutral' as const,
    tools: ['Risk of Bias', 'Quality Appraisal', 'Checklist Workflows'],
    note: 'Assessment of methodological quality and evidence trustworthiness.',
  },
  {
    name: 'Data extraction',
    status: 'Planned',
    tone: 'neutral' as const,
    tools: ['Extraction Forms', 'PDF to Structured Data', 'Excel Export'],
    note: 'Capture the information needed for synthesis and reporting.',
  },
  {
    name: 'Statistical synthesis',
    status: 'Planned',
    tone: 'neutral' as const,
    tools: ['Meta-analysis', 'Forest Plots', 'Subgroup Analysis'],
    note: 'Perform quantitative synthesis and analytical modelling.',
  },
  {
    name: 'Discussion & conclusion',
    status: 'Planned',
    tone: 'neutral' as const,
    tools: ['Interpretation Workspace', 'Evidence Summary', 'Final Outputs'],
    note: 'Turn results into a coherent scientific narrative and final outputs.',
  },
];

const QUICK_STATS = [
  { label: 'Projects', value: '1' },
  { label: 'Active phase', value: 'Screening' },
  { label: 'Live tool', value: 'PDF Fetcher' },
  { label: 'Data engine', value: 'SQLite' },
];

/* ─── SVG components ──────────────────────────────────────────────────── */

/**
 * PrismaLab full logo — dark variant (for landing, #111111 background).
 * No background rect; fills transparent so the page bg shows through.
 */
function PrismaLabLogoDark() {
  return (
    <svg
      viewBox="0 0 520 128"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="PrismaLab — research synthesis platform"
      style={{ display: 'block', overflow: 'visible' }}
    >
      {/* Prism */}
      <polygon points="106,15 58,98 154,98" fill="#1E1E1E" stroke="#585858" strokeWidth="1" />
      {/* Input beam */}
      <line x1="18" y1="62" x2="79" y2="62" stroke="#585858" strokeWidth="1.5" strokeLinecap="round" />
      {/* Emission point */}
      <circle cx="133" cy="62" r="3.5" fill="#585858" />
      {/* Spectrum rays */}
      <line x1="133" y1="62" x2="235" y2="22" stroke="#7F77DD" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="238" y2="44" stroke="#378ADD" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="240" y2="62" stroke="#1D9E75" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="238" y2="80" stroke="#EF9F27" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="235" y2="102" stroke="#D85A30" strokeWidth="2.5" strokeLinecap="round" />
      {/* Wordmark */}
      <text
        x="258" y="79"
        fontFamily="'DM Sans', -apple-system, sans-serif"
        fontSize="44"
      >
        <tspan fontWeight="500" fill="#FFFFFF">Prisma</tspan>
        <tspan fontWeight="300" fill="#5DCAA5" dx="4">Lab</tspan>
      </text>
      {/* Tagline */}
      <text
        x="259" y="106"
        fontFamily="'DM Sans', -apple-system, sans-serif"
        fontSize="12.5"
        fontWeight="400"
        fill="rgba(255,255,255,0.35)"
        letterSpacing="2"
      >
        research synthesis platform
      </text>
    </svg>
  );
}

/**
 * PrismaLab icon mark — light variant (for sidebar, white background).
 * viewBox crops to the prism + rays region only.
 * Aspect ratio 198:98 ≈ 2:1 → rendered at 52×26.
 */
function PrismaMarkLight() {
  return (
    <svg
      width="52"
      height="26"
      viewBox="48 8 198 98"
      xmlns="http://www.w3.org/2000/svg"
      className="brand-mark"
      aria-hidden="true"
    >
      <polygon points="106,15 58,98 154,98" fill="#F4F3EF" stroke="#CBCAC3" strokeWidth="1" />
      <line x1="18" y1="62" x2="79" y2="62" stroke="#CBCAC3" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="133" cy="62" r="3.5" fill="#CBCAC3" />
      <line x1="133" y1="62" x2="235" y2="22" stroke="#7F77DD" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="238" y2="44" stroke="#378ADD" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="240" y2="62" stroke="#1D9E75" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="238" y2="80" stroke="#EF9F27" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="235" y2="102" stroke="#D85A30" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

/**
 * Ray icon — 38px (chat header / sidebar size).
 * Circular mark with 5 spectrum rays. Dark mode.
 * Source: docs/assistants/ray/ray-banner-lockups.html
 */
function RayIconSm() {
  return (
    <svg
      width="38"
      height="38"
      viewBox="-19 -19 38 38"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      style={{ flexShrink: 0, display: 'block' }}
    >
      <circle r="18" fill="#1D2028" stroke="#2C3040" strokeWidth=".6" />
      <line x1="-15" y1="0" x2="-5" y2="0" stroke="#3A4250" strokeWidth="1.3" strokeLinecap="round" />
      <circle cx="-5" cy="0" r="1.6" fill="#50586A" />
      <line x1="-5" y1="0" x2="10"  y2="-12" stroke="#7F77DD" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="-5" y1="0" x2="13"  y2="-5"  stroke="#378ADD" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="-5" y1="0" x2="14"  y2="0"   stroke="#1D9E75" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="-5" y1="0" x2="13"  y2="5"   stroke="#EF9F27" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="-5" y1="0" x2="10"  y2="12"  stroke="#D85A30" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

/* ─── Small components ────────────────────────────────────────────────── */

function Badge({ text, tone }: { text: string; tone: 'neutral' | 'active' | 'warning' }) {
  return <span className={`badge badge-${tone}`}>{text}</span>;
}

function RayStatusDot() {
  return (
    <span
      className="ray-status-dot ray-status-dot--active-dark"
      aria-label="Online"
    />
  );
}

/* ─── Landing page ────────────────────────────────────────────────────── */

function LandingPage({ onEnter }: { onEnter: () => void }) {
  return (
    <div className="landing">
      <div className="landing-center">
        <div className="landing-logo-wrap">
          <PrismaLabLogoDark />
        </div>
        <div className="landing-actions">
          <button className="btn-landing-primary" onClick={onEnter}>
            Open Project
          </button>
          <button className="btn-landing-ghost" onClick={onEnter}>
            Import Existing Project
          </button>
        </div>
      </div>
      <p className="landing-version">prototype · v0.1</p>
    </div>
  );
}

/* ─── App dashboard ───────────────────────────────────────────────────── */

function AppDashboard() {
  return (
    <main className="app-shell">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        {/* Brand lockup: icon mark + wordmark */}
        <div className="sidebar-brand">
          <div className="brand-lockup">
            <PrismaMarkLight />
            <span className="brand-wordmark">
              <span className="brand-prisma">Prisma</span>
              <span className="brand-lab">Lab</span>
            </span>
          </div>
        </div>

        {/* Project info */}
        <div className="sidebar-section">
          <div className="sidebar-label">Project</div>
          <div className="sidebar-project">My Project</div>
          <div className="sidebar-note">Local project prototype</div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <button className="nav-item nav-item-active">Dashboard</button>
          <button className="nav-item">Projects</button>
          <button className="nav-item">Workflow Phases</button>
          <button className="nav-item">Tools</button>
          <button className="nav-item">Database</button>
          <button className="nav-item">Settings</button>
        </nav>

        {/* Ray assistant — pinned to sidebar bottom */}
        <div className="ray-sidebar-card">
          <div className="ray-card-inner">
            <RayIconSm />
            <div className="ray-text-block">
              <div className="ray-name-row">
                <span className="ray-name">Ray</span>
                <RayStatusDot />
              </div>
              <span className="ray-desc">Research Assistant</span>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Content ── */}
      <section className="content">
        <header className="hero">
          <div className="hero-kicker">PrismaLab prototype</div>
          <h1 className="hero-title">
            A project-first workspace for the full meta-analysis workflow
          </h1>
          <p className="hero-copy">
            Organised by meta-analysis phases rather than a flat list of tools. Each phase exposes
            its own workspace, current status, and relevant tools, while a local database keeps the
            project alive across years and collaborators.
          </p>
          <div className="hero-actions">
            <button className="primary-button">Open Project</button>
            <button className="secondary-button">Import Existing Project</button>
          </div>
        </header>

        <section className="panel">
          <div className="panel-title">Quick status</div>
          <div className="stats-grid">
            {QUICK_STATS.map((item) => (
              <div className="stat-card" key={item.label}>
                <div className="stat-label">{item.label}</div>
                <div className="stat-value">{item.value}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-title">Workflow phases</div>
          <div className="phase-list">
            {WORKFLOW_PHASES.map((phase, index) => (
              <article className="phase-card" key={phase.name}>
                <span
                  className="phase-accent"
                  style={{ background: PHASE_ACCENTS[index] }}
                  aria-hidden="true"
                />
                <div className="phase-top">
                  <div>
                    <div className="phase-index">Phase {index + 1}</div>
                    <h2 className="phase-name">{phase.name}</h2>
                  </div>
                  <Badge text={phase.status} tone={phase.tone} />
                </div>
                <p className="phase-note">{phase.note}</p>
                <div className="tool-row">
                  {phase.tools.map((tool) => (
                    <span className="tool-chip" key={tool}>{tool}</span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}

/* ─── Root ────────────────────────────────────────────────────────────── */

export default function HomePage() {
  const [view, setView] = useState<'landing' | 'app'>('landing');
  return view === 'landing'
    ? <LandingPage onEnter={() => setView('app')} />
    : <AppDashboard />;
}
