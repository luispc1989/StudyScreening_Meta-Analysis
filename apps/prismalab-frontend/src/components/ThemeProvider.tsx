import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark" | "system";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (t: Theme) => void;
  resolved: "light" | "dark";
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "system",
  setTheme: () => {},
  resolved: "light",
});

export function useTheme() {
  return useContext(ThemeContext);
}

function getSystemTheme(): "light" | "dark" {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function temporarilyDisableTransitions() {
  if (typeof window === "undefined") return;
  const style = document.createElement("style");
  style.appendChild(
    document.createTextNode(
      `*,
       *::before,
       *::after {
         transition: none !important;
         animation: none !important;
       }`,
    ),
  );
  document.head.appendChild(style);

  window.getComputedStyle(document.body);

  window.setTimeout(() => {
    document.head.removeChild(style);
  }, 40);
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") return "system";
    return (localStorage.getItem("prismalab-theme") as Theme) || "system";
  });
  const [resolved, setResolved] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") return "light";
    const datasetTheme = document.documentElement.dataset.theme;
    if (datasetTheme === "light" || datasetTheme === "dark") {
      return datasetTheme;
    }
    const stored = (localStorage.getItem("prismalab-theme") as Theme) || "system";
    return stored === "system" ? getSystemTheme() : stored;
  });

  const setTheme = (t: Theme) => {
    setThemeState(t);
    if (typeof window !== "undefined") {
      localStorage.setItem("prismalab-theme", t);
    }
  };

  useEffect(() => {
    temporarilyDisableTransitions();
    const r = theme === "system" ? getSystemTheme() : theme;
    setResolved(r);
    document.documentElement.classList.toggle("dark", r === "dark");
    document.documentElement.dataset.theme = r;

    if (theme === "system") {
      const mq = window.matchMedia("(prefers-color-scheme: dark)");
      const handler = (e: MediaQueryListEvent) => {
        setResolved(e.matches ? "dark" : "light");
        document.documentElement.classList.toggle("dark", e.matches);
        document.documentElement.dataset.theme = e.matches ? "dark" : "light";
      };
      mq.addEventListener("change", handler);
      return () => mq.removeEventListener("change", handler);
    }
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolved }}>
      {children}
    </ThemeContext.Provider>
  );
}
