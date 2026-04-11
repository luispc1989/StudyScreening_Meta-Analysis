import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { PrismaLabLogo } from "@/components/PrismaLabLogo";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { registerUser, setStoredUser } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "Create Account - PrismaLab" },
      { name: "description", content: "Register for PrismaLab research synthesis platform" },
    ],
  }),
  component: RegisterPage,
});

function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ fullName: "", email: "", username: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [remember, setRemember] = useState(true);

  const update = (field: string, value: string) => setForm((p) => ({ ...p, [field]: value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) {
      setError("Passwords do not match");
      return;
    }
    if (form.password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    try {
      registerUser({ fullName: form.fullName, email: form.email, username: form.username, password: form.password });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account");
      return;
    }
    setStoredUser({ fullName: form.fullName, email: form.email, username: form.username }, remember);
    navigate({ to: "/app/dashboard" });
  };

  const fields = [
    { id: "fullName", label: "Full name", type: "text", placeholder: "Enter your full name" },
    { id: "email", label: "Email", type: "email", placeholder: "researcher@institution.edu" },
    { id: "username", label: "Username", type: "text", placeholder: "Choose a username" },
    { id: "password", label: "Password", type: "password", placeholder: "At least 6 characters" },
    { id: "confirm", label: "Confirm password", type: "password", placeholder: "Repeat your password" },
  ];

  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="absolute inset-0 bg-white dark:bg-[#111111]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.05),transparent_30%),radial-gradient(circle_at_bottom,rgba(127,119,221,0.04),transparent_24%)] dark:bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.07),transparent_30%),radial-gradient(circle_at_bottom,rgba(127,119,221,0.06),transparent_24%)]" />
      <div className="absolute inset-3 rounded-[2rem] border border-[#e7e2d8] bg-white/98 shadow-[0_18px_50px_rgba(40,34,24,0.05)] dark:border-[#1c1c1a] dark:bg-[#111111]/98 dark:shadow-[0_24px_80px_rgba(0,0,0,0.28)]" />
      <div className="pointer-events-none absolute left-1/2 top-[54%] h-[34rem] w-[46rem] -translate-x-1/2 -translate-y-1/2 rounded-[3rem] bg-[radial-gradient(circle,rgba(255,255,255,0.72)_0%,rgba(255,255,255,0.36)_48%,transparent_80%)] blur-3xl dark:bg-[radial-gradient(circle,rgba(26,26,26,0.42)_0%,rgba(17,17,17,0.12)_52%,transparent_82%)]" />

      <div className="relative flex min-h-screen flex-col">
        <div className="flex items-center justify-end p-6">
          <ThemeSwitcher compact />
        </div>

        <div className="flex flex-1 items-center justify-center px-6 pb-16">
          <div className="grid w-full max-w-[74rem] justify-items-center">
            <div className="mx-auto flex w-full max-w-7xl justify-center text-center">
              <PrismaLabLogo showTagline size="lg" tone="auto" className="w-full max-w-[64rem]" />
            </div>

            <div className="relative mx-auto mt-7 w-full max-w-[36rem] rounded-[1.75rem] border border-[#ece6da] bg-white/80 px-8 py-8 shadow-[0_10px_30px_rgba(40,34,24,0.05)] backdrop-blur-[10px] dark:border-[#242424] dark:bg-[#151515]/84 dark:shadow-[0_14px_34px_rgba(0,0,0,0.22)]">
              <div className="space-y-7">
              <div className="space-y-2 text-left">
                <h1 className="text-4xl font-medium tracking-tight text-foreground">Create your account</h1>
                <p className="max-w-2xl text-base text-muted-foreground">
                  Set up your local PrismaLab workspace. Your email will support future in-app actions, including direct author contact during screening workflows.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="rounded-xl border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {error}
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                  {fields.map(({ id, label, type, placeholder }) => (
                    <div key={id} className={`space-y-2.5 ${id === "email" || id === "confirm" ? "md:col-span-2" : ""}`}>
                      <Label htmlFor={id} className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                        {label}
                      </Label>
                      <Input
                        id={id}
                        type={type}
                        value={form[id as keyof typeof form]}
                        onChange={(e) => update(id, e.target.value)}
                        placeholder={placeholder}
                        className="h-13 rounded-xl border-border/80 bg-card/70 px-4 shadow-none"
                        required
                      />
                    </div>
                  ))}
                </div>

                <div className="flex items-center gap-3 pt-1">
                  <input
                    type="checkbox"
                    id="remember-register"
                    checked={remember}
                    onChange={(e) => setRemember(e.target.checked)}
                    className="h-4 w-4 rounded border-border bg-background accent-[var(--color-brand-deep)]"
                  />
                  <Label htmlFor="remember-register" className="cursor-pointer text-base text-muted-foreground">
                    Keep me signed in on this PC
                  </Label>
                </div>

                <Button type="submit" className="mt-2 h-14 w-full rounded-xl border border-border bg-transparent text-lg font-medium text-foreground hover:bg-card/80">
                  Create profile
                </Button>
              </form>

              <div className="pt-1 text-center">
                <p className="text-base text-muted-foreground">
                  Already have an account?{" "}
                  <Link to="/login" className="font-medium text-brand hover:text-brand-deep transition-colors">
                    Sign in
                  </Link>
                </p>
              </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
