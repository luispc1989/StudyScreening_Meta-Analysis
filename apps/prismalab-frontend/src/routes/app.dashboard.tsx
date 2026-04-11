import { createFileRoute, Link } from "@tanstack/react-router";
import { getStoredUser } from "@/lib/auth";
import {
  ArrowRight,
  BarChart3,
  Clock3,
  Database,
  FileCheck,
  FileQuestion,
  FolderOpen,
  MessageSquareText,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export const Route = createFileRoute("/app/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard - PrismaLab" },
      { name: "description", content: "PrismaLab workspace dashboard" },
    ],
  }),
  component: DashboardPage,
});

const phases = [
  {
    id: "question",
    label: "Question Definition",
    icon: FileQuestion,
    color: "#7F77DD",
    description: "Define your PICO and frame the methodological scope of the project.",
    status: "Not started",
  },
  {
    id: "search",
    label: "Literature Search",
    icon: Search,
    color: "#378ADD",
    description: "Import records from bibliographic sources and preserve source provenance.",
    status: "Not started",
  },
  {
    id: "screening",
    label: "Study Screening",
    icon: FileCheck,
    color: "#1D9E75",
    description: "Move from title/abstract review to full-text and PDF workflows.",
    status: "Ready",
  },
  {
    id: "appraisal",
    label: "Critical Appraisal",
    icon: ShieldCheck,
    color: "#EF9F27",
    description: "Assess study quality and risk of bias with transparent criteria.",
    status: "Not started",
  },
  {
    id: "extraction",
    label: "Data Extraction",
    icon: Database,
    color: "#D85A30",
    description: "Capture structured variables and preserve extraction decisions.",
    status: "Not started",
  },
  {
    id: "synthesis",
    label: "Statistical Synthesis",
    icon: BarChart3,
    color: "#6B5FC7",
    description: "Prepare synthesis-ready datasets, models, and outputs.",
    status: "Not started",
  },
  {
    id: "discussion",
    label: "Discussion & Conclusion",
    icon: MessageSquareText,
    color: "#4A7EB5",
    description: "Translate results into findings, implications, and final reporting.",
    status: "Not started",
  },
];

const quickActions = [
  {
    label: "Start a new project",
    description: "Create a fresh PrismaLab workspace with local persistence.",
    icon: Plus,
  },
  {
    label: "Open an existing project",
    description: "Reconnect to a project and continue from its saved workflow state.",
    icon: FolderOpen,
  },
  {
    label: "Continue study screening",
    description: "Jump directly to PDF Fetcher and screening-related work.",
    icon: FileCheck,
    to: "/app/$phaseId" as const,
    params: { phaseId: "screening" },
  },
];

function DashboardPage() {
  const user = getStoredUser();
  const firstName = user?.fullName.split(" ")[0] || "Researcher";

  return (
    <div className="mx-auto max-w-7xl space-y-8 px-6 py-6 xl:px-8 xl:py-8">
      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(18rem,0.8fr)]">
        <div className="rounded-[1.75rem] border border-border bg-card/95 p-6 shadow-[0_16px_40px_rgba(25,20,14,0.04)]">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-2xl space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-background/80 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.24em] text-muted-foreground">
                <Sparkles className="h-3.5 w-3.5 text-brand-deep" />
                PrismaLab Workspace
              </div>
              <div className="space-y-2">
                <h1 className="text-2xl font-medium tracking-tight text-foreground xl:text-[2rem]">
                  Welcome back, {firstName}
                </h1>
                <p className="max-w-xl text-sm leading-6 text-muted-foreground xl:text-[0.95rem]">
                  PrismaLab is ready, but there is no active project yet. Start a new workspace or reopen an existing
                  one to anchor the full meta-analysis workflow around a persistent local project record.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <button className="inline-flex h-11 items-center justify-center rounded-xl border border-border bg-background px-4 text-sm font-medium text-foreground transition-colors hover:bg-secondary">
                Open project
              </button>
              <button className="inline-flex h-11 items-center justify-center rounded-xl bg-brand-deep px-4 text-sm font-medium text-background transition-colors hover:bg-brand">
                New project
              </button>
            </div>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            <DashboardStat label="Active project" value="None selected" hint="Choose or create a workspace" />
            <DashboardStat label="Source of truth" value="Local-first" hint="Project memory will persist locally" />
            <DashboardStat label="Current priority" value="Project setup" hint="No workflow phase has started yet" />
          </div>
        </div>

        <div className="rounded-[1.75rem] border border-border bg-card/95 p-5 shadow-[0_16px_40px_rgba(25,20,14,0.04)]">
          <div className="space-y-1">
            <p className="text-[11px] font-medium uppercase tracking-[0.24em] text-muted-foreground">Next actions</p>
            <h2 className="text-base font-medium text-foreground">Get this workspace moving</h2>
          </div>

          <div className="mt-4 space-y-3">
            {quickActions.map((action) => {
              const Icon = action.icon;
              const content = (
                <>
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-xl bg-brand-subtle text-brand-deep">
                      <Icon className="h-4.5 w-4.5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground">{action.label}</p>
                      <p className="mt-1 text-xs leading-5 text-muted-foreground">{action.description}</p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-1 text-xs font-medium text-brand-deep">
                    <span>Open</span>
                    <ArrowRight className="h-3 w-3" />
                  </div>
                </>
              );

              if (action.to) {
                return (
                  <Link
                    key={action.label}
                    to={action.to}
                    params={action.params}
                    className="block rounded-2xl border border-border bg-background/75 p-4 transition-all duration-200 hover:border-brand/30 hover:bg-background"
                  >
                    {content}
                  </Link>
                );
              }

              return (
                <button
                  key={action.label}
                  type="button"
                  className="w-full rounded-2xl border border-border bg-background/75 p-4 text-left transition-all duration-200 hover:border-brand/30 hover:bg-background"
                >
                  {content}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      <section className="rounded-[1.75rem] border border-border bg-card/95 p-5 shadow-[0_16px_40px_rgba(25,20,14,0.04)]">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.24em] text-muted-foreground">Meta-analysis workflow</p>
            <h2 className="mt-1 text-base font-medium text-foreground">Phase-based platform structure</h2>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock3 className="h-3.5 w-3.5" />
            <span>Projects will persist locally across sessions</span>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {phases.map((phase, index) => {
            const Icon = phase.icon;
            return (
              <Link
                key={phase.id}
                to="/app/$phaseId"
                params={{ phaseId: phase.id }}
                className="group rounded-2xl border border-border bg-background/75 p-4 transition-all duration-200 hover:border-brand/20 hover:bg-background hover:shadow-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-xl"
                    style={{ backgroundColor: `${phase.color}16` }}
                  >
                    <Icon className="h-4.5 w-4.5" style={{ color: phase.color }} />
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] font-medium tracking-[0.18em] text-muted-foreground">
                      {String(index + 1).padStart(2, "0")}
                    </p>
                    <p className="mt-1 text-[11px] text-muted-foreground">{phase.status}</p>
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  <h3 className="text-sm font-medium text-foreground">{phase.label}</h3>
                  <p className="text-xs leading-5 text-muted-foreground">{phase.description}</p>
                </div>

                <div className="mt-4 flex items-center gap-1 text-xs font-medium text-muted-foreground transition-colors group-hover:text-brand-deep">
                  <span>Open phase</span>
                  <ArrowRight className="h-3 w-3" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <div className="rounded-[1.75rem] border border-border bg-card/95 p-5 shadow-[0_16px_40px_rgba(25,20,14,0.04)]">
          <div className="space-y-1">
            <p className="text-[11px] font-medium uppercase tracking-[0.24em] text-muted-foreground">Project memory</p>
            <h2 className="text-base font-medium text-foreground">What PrismaLab will preserve</h2>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <MemoryCard
              title="Imported records"
              description="Bibliographic records from different sources will converge into one local project memory."
            />
            <MemoryCard
              title="Screening decisions"
              description="Manual review decisions, notes, and residual checks will remain attached to the project."
            />
            <MemoryCard
              title="PDF workflows"
              description="PDF Fetcher and future full-text actions will live inside the Study Screening phase."
            />
            <MemoryCard
              title="Reopenable projects"
              description="A project should be reopenable years later without losing what has already been evaluated."
            />
          </div>
        </div>

        <div className="rounded-[1.75rem] border border-border bg-card/95 p-5 shadow-[0_16px_40px_rgba(25,20,14,0.04)]">
          <div className="space-y-1">
            <p className="text-[11px] font-medium uppercase tracking-[0.24em] text-muted-foreground">Recent activity</p>
            <h2 className="text-base font-medium text-foreground">No project activity yet</h2>
          </div>

          <div className="mt-6 rounded-2xl border border-dashed border-border/80 bg-background/70 p-5">
            <p className="text-sm leading-6 text-muted-foreground">
              Activity will appear here once a project is opened and workflow steps begin to generate local history,
              imported records, screening events, and assistant interactions.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function DashboardStat({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="rounded-2xl border border-border/80 bg-background/75 p-4">
      <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
      <p className="mt-1 text-xs leading-5 text-muted-foreground">{hint}</p>
    </div>
  );
}

function MemoryCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-border/80 bg-background/75 p-4">
      <h3 className="text-sm font-medium text-foreground">{title}</h3>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{description}</p>
    </div>
  );
}
