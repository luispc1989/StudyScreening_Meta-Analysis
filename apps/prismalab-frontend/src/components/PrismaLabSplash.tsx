import { PrismaLabLogo } from "@/components/PrismaLabLogo";

export function PrismaLabSplash({
  label = "Loading PrismaLab",
}: {
  label?: string;
}) {
  return (
    <div
      className="relative flex min-h-screen items-center justify-center overflow-hidden bg-white text-foreground dark:bg-[#111111]"
      aria-label={label}
      role="status"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.05),transparent_30%),radial-gradient(circle_at_bottom,rgba(55,138,221,0.04),transparent_24%)] dark:bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.07),transparent_30%),radial-gradient(circle_at_bottom,rgba(55,138,221,0.06),transparent_24%)]" />
      <div className="absolute inset-3 rounded-[2rem] border border-[#e7e2d8] bg-white/98 shadow-[0_18px_50px_rgba(40,34,24,0.05)] dark:border-[#1c1c1a] dark:bg-[#111111]/98 dark:shadow-[0_24px_80px_rgba(0,0,0,0.28)]" />

      <div className="relative z-10 flex w-full max-w-3xl flex-col items-center px-6 text-center">
        <PrismaLabLogo
          showTagline
          size="lg"
          tone="auto"
          className="w-full max-w-[24rem] sm:max-w-[30rem] md:max-w-[34rem]"
        />

        <div className="mt-8 flex items-center gap-2">
          <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-brand/85 [animation-delay:0ms]" />
          <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-brand/65 [animation-delay:180ms]" />
          <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-brand/45 [animation-delay:360ms]" />
        </div>
      </div>
    </div>
  );
}
