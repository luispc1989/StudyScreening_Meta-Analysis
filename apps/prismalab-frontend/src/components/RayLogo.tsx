type LogoTone = "auto" | "light" | "dark";

function ThemedAsset({
  lightSrc,
  darkSrc,
  alt,
  className = "",
  tone = "auto",
}: {
  lightSrc: string;
  darkSrc: string;
  alt: string;
  className?: string;
  tone?: LogoTone;
}) {
  if (tone === "light") {
    return <img src={lightSrc} alt={alt} className={className} />;
  }

  if (tone === "dark") {
    return <img src={darkSrc} alt={alt} className={className} />;
  }

  return (
    <>
      <img src={lightSrc} alt={alt} className={`${className} block dark:hidden`} />
      <img src={darkSrc} alt={alt} className={`${className} hidden dark:block`} />
    </>
  );
}

export function RayMark({
  className = "",
  tone = "auto",
}: {
  className?: string;
  tone?: LogoTone;
}) {
  return (
    <ThemedAsset
      lightSrc="/ray-mark-dark.svg"
      darkSrc="/ray-mark-light.svg"
      alt="Ray assistant mark"
      className={className}
      tone={tone}
    />
  );
}

export function RayIcon({
  className = "",
  tone = "auto",
}: {
  className?: string;
  tone?: LogoTone;
}) {
  return (
    <ThemedAsset
      lightSrc="/ray-icon-light-80.svg"
      darkSrc="/ray-icon-dark-80.svg"
      alt="Ray assistant icon"
      className={className}
      tone={tone}
    />
  );
}

export function RayLogo({
  className = "",
  tone = "auto",
}: {
  className?: string;
  tone?: LogoTone;
}) {
  return (
    <ThemedAsset
      lightSrc="/ray-logo-dark.svg"
      darkSrc="/ray-logo-light.svg"
      alt="Ray research assistant"
      className={className}
      tone={tone}
    />
  );
}

export function RayAvatar({
  className = "",
  tone = "auto",
  size = "lg",
}: {
  className?: string;
  tone?: LogoTone;
  size?: "sm" | "md" | "lg" | "xl";
}) {
  const lightSrc =
    size === "sm"
      ? "/ray-avatar-light-32.png"
      : size === "md"
        ? "/ray-avatar-light-40.png"
        : size === "lg"
          ? "/ray-avatar-light-48.png"
          : "/ray-avatar-light-80.png";
  const darkSrc =
    size === "sm"
      ? "/ray-avatar-dark-32.png"
      : size === "md"
        ? "/ray-avatar-dark-40.png"
        : size === "lg"
          ? "/ray-avatar-dark-48.png"
          : "/ray-avatar-dark-80.png";

  return (
    <ThemedAsset
      lightSrc={lightSrc}
      darkSrc={darkSrc}
      alt="Ray assistant avatar"
      className={className}
      tone={tone}
    />
  );
}
