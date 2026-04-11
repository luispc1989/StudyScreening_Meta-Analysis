type LogoTone = "auto" | "light" | "dark";

function FullLogo({
  tone,
}: {
  tone: "light" | "dark";
}) {
  const isLight = tone === "light";
  const prismFill = isLight ? "#F4F3EF" : "#1E1E1E";
  const prismStroke = isLight ? "#CBCAC3" : "#585858";
  const textPrimary = isLight ? "#1C1C1A" : "#FFFFFF";
  const tagline = isLight ? "#888780" : "rgba(255,255,255,0.35)";

  return (
    <svg viewBox="0 0 520 128" xmlns="http://www.w3.org/2000/svg" className="h-auto w-full">
      <polygon points="106,15 58,98 154,98" fill={prismFill} stroke={prismStroke} strokeWidth="1" />
      <line x1="18" y1="62" x2="79" y2="62" stroke={prismStroke} strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="133" cy="62" r="3.5" fill={prismStroke} />
      <line x1="133" y1="62" x2="235" y2="22" stroke="#7F77DD" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="238" y2="44" stroke="#378ADD" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="240" y2="62" stroke="#1D9E75" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="238" y2="80" stroke="#EF9F27" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="133" y1="62" x2="235" y2="102" stroke="#D85A30" strokeWidth="2.5" strokeLinecap="round" />
      <text x="258" y="79" fontFamily="'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif" fontSize="44">
        <tspan fontWeight="500" fill={textPrimary}>Prisma</tspan>
        <tspan fontWeight="300" fill="#5DCAA5" dx="4">Lab</tspan>
      </text>
      <text
        x="259"
        y="106"
        fontFamily="'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif"
        fontSize="12.5"
        fontWeight="400"
        fill={tagline}
        letterSpacing="2"
      >
        research synthesis platform
      </text>
    </svg>
  );
}

export function PrismaLabMark({
  className = "",
  size = 80,
  tone = "auto",
}: {
  className?: string;
  size?: number;
  tone?: LogoTone;
}) {
  const shared = {
    width: size,
    viewBox: "48 8 198 98",
    xmlns: "http://www.w3.org/2000/svg",
    className,
  };

  if (tone === "light") {
    return (
      <svg {...shared}>
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

  if (tone === "dark") {
    return (
      <svg {...shared}>
        <polygon points="106,15 58,98 154,98" fill="#1E1E1E" stroke="#585858" strokeWidth="1" />
        <line x1="18" y1="62" x2="79" y2="62" stroke="#585858" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="133" cy="62" r="3.5" fill="#585858" />
        <line x1="133" y1="62" x2="235" y2="22" stroke="#7F77DD" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="238" y2="44" stroke="#378ADD" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="240" y2="62" stroke="#1D9E75" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="238" y2="80" stroke="#EF9F27" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="235" y2="102" stroke="#D85A30" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
    );
  }

  return (
    <>
      <svg {...shared} className={`${className} block dark:hidden`}>
        <polygon points="106,15 58,98 154,98" fill="#F4F3EF" stroke="#CBCAC3" strokeWidth="1" />
        <line x1="18" y1="62" x2="79" y2="62" stroke="#CBCAC3" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="133" cy="62" r="3.5" fill="#CBCAC3" />
        <line x1="133" y1="62" x2="235" y2="22" stroke="#7F77DD" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="238" y2="44" stroke="#378ADD" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="240" y2="62" stroke="#1D9E75" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="238" y2="80" stroke="#EF9F27" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="235" y2="102" stroke="#D85A30" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
      <svg {...shared} className={`${className} hidden dark:block`}>
        <polygon points="106,15 58,98 154,98" fill="#1E1E1E" stroke="#585858" strokeWidth="1" />
        <line x1="18" y1="62" x2="79" y2="62" stroke="#585858" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="133" cy="62" r="3.5" fill="#585858" />
        <line x1="133" y1="62" x2="235" y2="22" stroke="#7F77DD" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="238" y2="44" stroke="#378ADD" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="240" y2="62" stroke="#1D9E75" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="238" y2="80" stroke="#EF9F27" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="133" y1="62" x2="235" y2="102" stroke="#D85A30" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
    </>
  );
}

export function PrismaLabWordmark({
  className = "",
  size = "md",
  tone = "auto",
}: {
  className?: string;
  showTagline?: boolean;
  size?: "sm" | "md" | "lg";
  tone?: LogoTone;
}) {
  const widthClass = size === "sm" ? "max-w-[16rem]" : size === "lg" ? "max-w-[64rem]" : "max-w-[24rem]";

  if (tone === "light" || tone === "dark") {
    return (
      <div className={`${widthClass} ${className}`} aria-label="PrismaLab research synthesis platform">
        <FullLogo tone={tone} />
      </div>
    );
  }

  return (
    <div className={`${widthClass} ${className}`} aria-label="PrismaLab research synthesis platform">
      <div className="block dark:hidden">
        <FullLogo tone="light" />
      </div>
      <div className="hidden dark:block">
        <FullLogo tone="dark" />
      </div>
    </div>
  );
}

export function PrismaLabLogo({
  className = "",
  size = "md",
  tone = "auto",
}: {
  className?: string;
  showTagline?: boolean;
  size?: "sm" | "md" | "lg";
  tone?: LogoTone;
}) {
  return <PrismaLabWordmark className={className} size={size} tone={tone} />;
}
