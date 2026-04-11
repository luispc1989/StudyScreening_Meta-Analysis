import { createFileRoute, useParams } from "@tanstack/react-router";
import {
  FileQuestion, Search, FileCheck, ShieldCheck, Database,
  BarChart3, MessageSquareText, Download, Upload, Filter
} from "lucide-react";

export const Route = createFileRoute("/app/$phaseId")({
  component: PhasePage,
});

const phaseMeta: Record<string, { label: string; icon: any; color: string; description: string }> = {
  question: { label: "Question Definition", icon: FileQuestion, color: "#7F77DD", description: "Define your research question using the PICO framework. Establish inclusion and exclusion criteria, outcomes of interest, and the scope of your systematic review." },
  search: { label: "Literature Search", icon: Search, color: "#378ADD", description: "Search multiple databases, import bibliographic records, manage duplicates, and document your search strategy for reproducibility." },
  screening: { label: "Study Screening", icon: FileCheck, color: "#1D9E75", description: "Screen studies by title and abstract, then by full text. Use PDF Fetcher to retrieve full-text articles. Track decisions and inter-rater reliability." },
  appraisal: { label: "Critical Appraisal", icon: ShieldCheck, color: "#EF9F27", description: "Assess the risk of bias and methodological quality of included studies using validated tools such as Cochrane RoB 2 or GRADE." },
  extraction: { label: "Data Extraction", icon: Database, color: "#D85A30", description: "Extract quantitative and qualitative data from included studies using structured forms. Export data for analysis." },
  synthesis: { label: "Statistical Synthesis", icon: BarChart3, color: "#6B5FC7", description: "Run meta-analyses, generate forest plots, assess heterogeneity, perform subgroup and sensitivity analyses." },
  discussion: { label: "Discussion & Conclusion", icon: MessageSquareText, color: "#4A7EB5", description: "Summarize key findings, discuss implications, limitations, and generate PRISMA-compliant reporting." },
};

function PhasePage() {
  const { phaseId } = Route.useParams();
  const meta = phaseMeta[phaseId] || phaseMeta.question;
  const Icon = meta.icon;
  const isScreening = phaseId === "screening";

  return (
    <div className="p-6 xl:p-8 max-w-5xl mx-auto space-y-6">
      {/* Phase header */}
      <div className="flex items-start gap-4">
        <div
          className="h-12 w-12 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: `${meta.color}15` }}
        >
          <Icon className="h-6 w-6" style={{ color: meta.color }} />
        </div>
        <div>
          <h1 className="text-xl font-medium text-foreground">{meta.label}</h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-xl leading-relaxed">
            {meta.description}
          </p>
        </div>
      </div>

      {/* Phase content area */}
      <div className="rounded-xl border border-border bg-card">
        <div className="border-b border-border px-5 py-3 flex items-center justify-between">
          <span className="text-xs font-medium tracking-[0.15em] uppercase text-muted-foreground">
            Workspace
          </span>
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
              <Upload className="h-3 w-3" />
              Import
            </button>
            <button className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
              <Download className="h-3 w-3" />
              Export
            </button>
          </div>
        </div>

        <div className="flex items-center justify-center py-16 text-sm text-muted-foreground">
          <div className="text-center space-y-2">
            <Icon className="h-8 w-8 mx-auto opacity-20" style={{ color: meta.color }} />
            <p>Open a project to begin working in this phase</p>
            <p className="text-xs">Data will be stored in your local database</p>
          </div>
        </div>
      </div>

      {/* Screening-specific: PDF Fetcher + sub-tools */}
      {isScreening && (
        <div className="space-y-4">
          <h3 className="text-xs font-medium tracking-[0.2em] uppercase text-muted-foreground">
            Screening Tools
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <ToolCard
              title="Title & Abstract Screening"
              description="Review titles and abstracts against your inclusion criteria"
              color="#1D9E75"
              icon={<Filter className="h-4 w-4" />}
            />
            <ToolCard
              title="Full-Text Screening"
              description="Detailed assessment of full-text articles for final inclusion"
              color="#1D9E75"
              icon={<FileCheck className="h-4 w-4" />}
            />
            <ToolCard
              title="PDF Fetcher"
              description="Automatically retrieve full-text PDFs from DOI or search results"
              color="#378ADD"
              icon={<Download className="h-4 w-4" />}
              highlight
            />
          </div>
        </div>
      )}
    </div>
  );
}

function ToolCard({ title, description, color, icon, highlight }: {
  title: string;
  description: string;
  color: string;
  icon: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl border p-4 transition-all duration-200 hover:shadow-sm ${
      highlight ? "border-spectrum-2/30 bg-spectrum-2/5" : "border-border bg-card"
    }`}>
      <div className="flex items-center gap-2 mb-2">
        <div
          className="h-7 w-7 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: `${color}15`, color }}
        >
          {icon}
        </div>
        <h4 className="text-sm font-medium">{title}</h4>
      </div>
      <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>
      <button className="mt-3 text-xs font-medium text-brand-deep hover:text-brand transition-colors">
        Open tool →
      </button>
    </div>
  );
}
