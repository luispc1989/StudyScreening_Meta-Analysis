import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PrismaLabLogo } from "@/components/PrismaLabLogo";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { getRememberedUser, loginUser, setStoredUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles } from "lucide-react";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign In - PrismaLab" },
      { name: "description", content: "Sign in to PrismaLab research synthesis platform" },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState(() => getRememberedUser() || "");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(!!getRememberedUser());
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const hasKnownProfile = !!getRememberedUser();

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (localStorage.getItem("prismalab-session") === "active") {
      navigate({ to: "/app/dashboard" });
    }
  }, [navigate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    setIsSubmitting(true);
    setError("");
    window.setTimeout(() => {
      const user = loginUser(username, password);
      if (!user) {
        setError("Invalid username or password");
        setIsSubmitting(false);
        return;
      }
      setStoredUser(user, remember);
      navigate({ to: "/app/dashboard" });
    }, 900);
  };

  const handleDevAccess = () => {
    setStoredUser(
      {
        fullName: "Luis Pinto Coelho",
        email: "luispc1989@prismalab.local",
        username: "luispc1989",
      },
      true,
    );
    navigate({ to: "/app/dashboard" });
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="absolute inset-0 bg-white dark:bg-[#111111]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.05),transparent_30%),radial-gradient(circle_at_bottom,rgba(55,138,221,0.04),transparent_24%)] dark:bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.07),transparent_30%),radial-gradient(circle_at_bottom,rgba(55,138,221,0.06),transparent_24%)]" />
      <div className="absolute inset-3 rounded-[2rem] border border-[#e7e2d8] bg-white/98 shadow-[0_18px_50px_rgba(40,34,24,0.05)] dark:border-[#1c1c1a] dark:bg-[#111111]/98 dark:shadow-[0_24px_80px_rgba(0,0,0,0.28)]" />
      <div className="pointer-events-none absolute left-1/2 top-[54%] h-[30rem] w-[42rem] -translate-x-1/2 -translate-y-1/2 rounded-[3rem] bg-[radial-gradient(circle,rgba(255,255,255,0.72)_0%,rgba(255,255,255,0.36)_48%,transparent_80%)] blur-3xl dark:bg-[radial-gradient(circle,rgba(26,26,26,0.42)_0%,rgba(17,17,17,0.12)_52%,transparent_82%)]" />

      <div className="relative flex min-h-screen flex-col">
        <div className="flex items-center justify-end px-4 pt-4 pb-2 sm:px-6 sm:pt-5 sm:pb-3">
          <ThemeSwitcher compact />
        </div>

        <div className="flex flex-1 items-start justify-center px-4 pb-8 pt-3 sm:px-6 sm:pb-10 sm:pt-4 lg:pb-12 xl:pt-5">
          <div className="grid w-full max-w-[78rem] justify-items-center">
            <div className="mx-auto flex w-full justify-center text-center">
              <PrismaLabLogo
                showTagline
                size="lg"
                tone="auto"
                className="w-full max-w-[22rem] sm:max-w-[28rem] md:max-w-[34rem] lg:max-w-[40rem] xl:max-w-[48rem] 2xl:max-w-[54rem]"
              />
            </div>

            <div className="relative mx-auto mt-4 w-full max-w-[28rem] rounded-[1.5rem] border border-[#e7ded0] bg-white/88 px-5 py-6 shadow-[0_16px_36px_rgba(40,34,24,0.06)] backdrop-blur-[10px] sm:mt-5 sm:max-w-[30rem] sm:px-7 sm:py-7 lg:max-w-[31rem] xl:mt-6 xl:max-w-[32rem] 2xl:max-w-[33rem] dark:border-[#242424] dark:bg-[#151515]/88 dark:shadow-[0_16px_36px_rgba(0,0,0,0.24)]">
              <div className="space-y-8">
              <div className="space-y-2 text-left">
                <h1 className="text-[1.7rem] font-medium tracking-tight leading-[1] text-foreground sm:text-[1.95rem] md:text-[2.2rem] md:whitespace-nowrap xl:text-[2.35rem]">
                  {hasKnownProfile ? "Welcome back" : "Access PrismaLab"}
                </h1>
                <p className="text-base text-muted-foreground sm:text-[1.05rem]">
                  {hasKnownProfile ? "Sign in to continue your research" : "Sign in or create your local research workspace"}
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                  <div className="rounded-xl border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {error}
                  </div>
                )}

                <div className="space-y-2.5">
                  <Label htmlFor="username" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                    Username
                  </Label>
                  <Input
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter your username"
                    className="h-14 rounded-xl border-border/80 bg-card/70 px-4 text-lg shadow-none"
                    required
                  />
                </div>

                <div className="space-y-2.5">
                  <Label htmlFor="password" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                    Password
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="h-14 rounded-xl border-border/80 bg-card/70 px-4 text-lg shadow-none"
                    required
                  />
                </div>

                <div className="flex items-center gap-3 pt-1">
                  <input
                    type="checkbox"
                    id="remember"
                    checked={remember}
                    onChange={(e) => setRemember(e.target.checked)}
                    className="h-4 w-4 rounded border-border bg-background accent-[var(--color-brand-deep)]"
                  />
                  <Label htmlFor="remember" className="cursor-pointer text-base text-muted-foreground">
                    Remember me
                  </Label>
                </div>

                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="h-14 w-full rounded-xl border border-border bg-transparent text-xl font-medium text-foreground hover:bg-card/80 disabled:opacity-100"
                >
                  Sign in
                </Button>
              </form>

              <div className="pt-2 text-center">
                <p className="text-base text-muted-foreground">
                  Don't have an account?{" "}
                  <Link to="/register" className="font-medium text-brand hover:text-brand-deep transition-colors">
                    Create account
                  </Link>
                </p>
                <button
                  type="button"
                  onClick={handleDevAccess}
                  className="mt-4 inline-flex items-center justify-center rounded-lg border border-dashed border-border px-3 py-1.5 text-xs font-medium tracking-[0.22em] text-muted-foreground transition-colors hover:border-brand/40 hover:text-brand-deep"
                >
                  DEV
                </button>
              </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {isSubmitting ? (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/82 backdrop-blur-sm dark:bg-background/88">
          <div className="relative flex h-28 w-28 items-center justify-center">
            <span className="absolute h-28 w-28 animate-ping rounded-full bg-brand/10" />
            <span className="absolute h-20 w-20 animate-pulse rounded-full border border-brand/30" />
            <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-card shadow-lg">
              <Sparkles className="h-8 w-8 text-brand animate-pulse" />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
