import { useMemo, useState } from "react";
import { AlertTriangle, Check, Copy, Download } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";

interface RecoveryKeyPanelProps {
  title: string;
  subtitle: string;
  recoveryKey: string;
  continueLabel: string;
  confirmationLabel: string;
  onContinue: () => void;
}

export function RecoveryKeyPanel({
  title,
  subtitle,
  recoveryKey,
  continueLabel,
  confirmationLabel,
  onContinue,
}: RecoveryKeyPanelProps) {
  const [confirmed, setConfirmed] = useState(false);
  const [copied, setCopied] = useState(false);
  const [downloaded, setDownloaded] = useState(false);

  const recoveryText = useMemo(
    () =>
      [
        "PrismaLab Recovery Key",
        "",
        "Important",
        "This recovery key is the only method available to recover access to your local PrismaLab account if you forget your password. It will only be shown once and cannot be retrieved later. Store it securely.",
        "",
        `Recovery Key: ${recoveryKey}`,
      ].join("\n"),
    [recoveryKey],
  );

  const handleCopy = async () => {
    await navigator.clipboard.writeText(recoveryKey);
    setCopied(true);
  };

  const handleDownload = () => {
    const blob = new Blob([recoveryText], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "prismalab-recovery-key.txt";
    anchor.click();
    URL.revokeObjectURL(url);
    setDownloaded(true);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-left">
        <h1 className="text-[1.7rem] font-medium tracking-tight leading-[1] text-foreground sm:text-[1.95rem] md:text-[2.2rem] xl:text-[2.35rem]">
          {title}
        </h1>
        <p className="text-base text-muted-foreground sm:text-[1.05rem]">{subtitle}</p>
      </div>

      <Alert className="border-amber-500/30 bg-amber-500/10 text-foreground dark:border-amber-400/30 dark:bg-amber-400/10">
        <AlertTriangle className="h-4 w-4 text-amber-700 dark:text-amber-300" />
        <AlertTitle>Important</AlertTitle>
        <AlertDescription>
          This recovery key is the only method available to recover access to your local PrismaLab account if you forget your password. It will only be shown once and cannot be retrieved later. Store it securely.
        </AlertDescription>
      </Alert>

      <div className="rounded-2xl border border-border/80 bg-card/75 p-5 text-center shadow-sm">
        <p className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">Recovery Key</p>
        <p className="mt-3 break-all font-mono text-lg font-medium tracking-[0.16em] text-foreground sm:text-xl">
          {recoveryKey}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Button
          type="button"
          variant="outline"
          className="h-12 rounded-xl text-base"
          onClick={handleCopy}
        >
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          {copied ? "Copied" : "Copy key"}
        </Button>
        <Button
          type="button"
          variant="outline"
          className="h-12 rounded-xl text-base"
          onClick={handleDownload}
        >
          {downloaded ? <Check className="h-4 w-4" /> : <Download className="h-4 w-4" />}
          {downloaded ? "Downloaded" : "Download .txt"}
        </Button>
      </div>

      <div className="flex items-start gap-3 rounded-xl border border-border/70 bg-background/70 px-4 py-3">
        <input
          type="checkbox"
          id="confirm-recovery-key"
          checked={confirmed}
          onChange={(e) => setConfirmed(e.target.checked)}
          className="mt-1 h-4 w-4 rounded border-border bg-background accent-[var(--color-brand-deep)]"
        />
        <Label htmlFor="confirm-recovery-key" className="cursor-pointer text-sm leading-6 text-muted-foreground">
          {confirmationLabel}
        </Label>
      </div>

      <Button
        type="button"
        disabled={!confirmed}
        className="h-14 w-full rounded-xl border border-border bg-transparent text-lg font-medium text-foreground hover:bg-card/80 disabled:cursor-not-allowed disabled:opacity-60"
        onClick={onContinue}
      >
        {continueLabel}
      </Button>
    </div>
  );
}
