import { createFileRoute } from "@tanstack/react-router";
import { getStoredUser } from "@/lib/auth";
import { Link } from "@tanstack/react-router";
import {
  FileQuestion, Search, FileCheck, ShieldCheck, Database,
  BarChart3, MessageSquareText, ArrowRight, FolderOpen, Clock
} from "lucide-react";

export const Route = createFileRoute("/app/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — PrismaLab" },
      { name: "description", content: "PrismaLab workspace dashboard" },
    ],
  }),
  component: DashboardPage,
});

const phases = [
  { id: "question", label: "Question Definition", icon: FileQuestion, color: "#7F77DD", description: "Define your PICO and research question" },
  { id: "search", label: "Literature Search", icon: Search, color: "#378ADD", description: "Search databases and import records" },
  { id: "screening", label: "Study Screening", icon: FileCheck, color: "#1D9E75", description: "Title/abstract and full-text screening" },
  { id: "appraisal", label: "Critical Appraisal", icon: ShieldCheck, color: "#EF9F27", description: "Assess risk of bias and quality" },
  { id: "extraction", label: "Data Extraction", icon: Database, color: "#D85A30", description: "Extract study data systematically" },
  { id: "synthesis", label: "Statistical Synthesis", icon: BarChart3, color: "#6B5FC7", description: "Run meta-analysis and generate outputs" },
  { id: "discussion", label: "Discussion & Conclusion", icon: MessageSquareText, color: "#4A7EB5", description: "Summarize findings and implications" },
];

function DashboardPage() {
  const user = getStoredUser();

  return (
    <div className="p-6 xl:p-8 max-w-6xl mx-auto space-y-8">
      {/* Welcome */}
      <div>
        <h1 className="text-xl font-medium text-foreground">
          Welcome back{user ? `, ${user.fullName.split(" ")[0]}` : ""}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Continue your research or start a new project
        </p>
      </div>

      {/* Active project card */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-brand-subtle flex items-center justify-center">
              <FolderOpen className="h-5 w-5 text-brand-deep" />
            </div>
            <div>
              <h2 className="text-sm font-medium">No active project</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Create or open a project to begin working
              </p>
            </div>
          </div>
          <button className="rounded-lg bg-brand-deep px-4 py-2 text-xs font-medium text-background hover:bg-brand transition-colors">
            New Project
          </button>
        </div>

        {/* Phase progress bar */}
        <div className="mt-5 flex gap-1">
          {phases.map((phase, i) => (
            <div
              key={phase.id}
              className="h-1.5 flex-1 rounded-full"
              style={{ backgroundColor: `${phase.color}20` }}
            />
          ))}
        </div>
        <div className="flex items-center gap-1.5 mt-2">
          <Clock className="h-3 w-3 text-muted-foreground" />
          <span className="text-[11px] text-muted-foreground">
            Projects will persist locally across sessions
          </span>
        </div>
      </div>

      {/* Workflow phases grid */}
      <div>
        <h3 className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground mb-4">
          Meta-Analysis Workflow
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {phases.map((phase, i) => {
            const Icon = phase.icon;
            return (
              <Link
                key={phase.id}
                to="/app/$phaseId"
                params={{ phaseId: phase.id }}
                className="group rounded-xl border border-border bg-card p-4 hover:border-border/80 hover:shadow-sm transition-all duration-200"
              >
                <div className="flex items-start justify-between mb-3">
                  <div
                    className="h-8 w-8 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${phase.color}15` }}
                  >
                    <Icon className="h-4 w-4" style={{ color: phase.color }} />
                  </div>
                  <span className="text-[10px] font-medium text-muted-foreground tracking-wider">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                </div>
                <h4 className="text-sm font-medium text-foreground mb-1">{phase.label}</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">{phase.description}</p>
                <div className="flex items-center gap-1 mt-3 text-xs text-muted-foreground group-hover:text-brand-deep transition-colors">
                  <span>Open</span>
                  <ArrowRight className="h-3 w-3" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent activity placeholder */}
      <div className="rounded-xl border border-border bg-card p-5">
        <h3 className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground mb-4">
          Recent Activity
        </h3>
        <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
          Activity will appear here as you work on projects
        </div>
      </div>
    </div>
  );
}
