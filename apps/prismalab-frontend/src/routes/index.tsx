import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { isLoggedIn } from "@/lib/auth";

export const Route = createFileRoute("/")({
  component: Index,
});

function Index() {
  if (typeof window !== "undefined") {
    if (isLoggedIn()) {
      window.location.href = "/app";
    } else {
      window.location.href = "/login";
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="h-5 w-5 rounded-full bg-brand animate-pulse" />
        <p className="text-sm text-muted-foreground">Loading PrismaLab...</p>
      </div>
    </div>
  );
}
