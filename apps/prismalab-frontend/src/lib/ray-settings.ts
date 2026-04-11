export type RayProviderMode = "ollama-local" | "ollama-api";

export interface RaySettings {
  mode: RayProviderMode;
  localEndpoint: string;
  localModel: string;
  apiEndpoint: string;
  apiKey: string;
  apiModel: string;
}

const DEFAULT_RAY_SETTINGS: RaySettings = {
  mode: "ollama-local",
  localEndpoint: "http://localhost:11434",
  localModel: "llama3.1:8b",
  apiEndpoint: "https://ollama.com/api",
  apiKey: "",
  apiModel: "llama3.1:8b",
};

function getRaySettingsKey(username: string) {
  return `prismalab-ray-settings:${username}`;
}

export function getDefaultRaySettings(): RaySettings {
  return { ...DEFAULT_RAY_SETTINGS };
}

export function loadRaySettings(username?: string | null): RaySettings {
  if (typeof window === "undefined" || !username) {
    return getDefaultRaySettings();
  }

  try {
    const raw = localStorage.getItem(getRaySettingsKey(username));
    if (!raw) return getDefaultRaySettings();
    const parsed = JSON.parse(raw) as Partial<RaySettings>;
    return {
      ...DEFAULT_RAY_SETTINGS,
      ...parsed,
    };
  } catch {
    return getDefaultRaySettings();
  }
}

export function saveRaySettings(username: string, settings: RaySettings) {
  if (typeof window === "undefined") return;
  localStorage.setItem(getRaySettingsKey(username), JSON.stringify(settings));
}
