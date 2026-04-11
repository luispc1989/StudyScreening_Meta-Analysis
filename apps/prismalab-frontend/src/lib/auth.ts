export interface User {
  fullName: string;
  email: string;
  username: string;
}

interface StoredUserRecord extends User {
  passwordHash?: string;
  recoveryKeyHash?: string;
  password?: string;
  recoveryKey?: string;
}

const USERS_KEY = "prismalab-users";
const USER_KEY = "prismalab-user";
const SESSION_KEY = "prismalab-session";
const REMEMBERED_USER_KEY = "prismalab-remembered-user";
const REMEMBER_ME_KEY = "prismalab-remember-me";

const DEV_USER: StoredUserRecord = {
  fullName: "Luis Pinto Coelho",
  email: "luispc1989@prismalab.local",
  username: "luispc1989",
  passwordHash: "78b250aa08412a350172d7b010a20ddfe996c06c8269c57145b054065e0fa797",
  recoveryKeyHash: "1e8aa6c7d1167652e57e3488a9f76d8f4f84ba7e80e96802dc963964dcee9091",
};

const RECOVERY_KEY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

function normalizeUsername(username: string) {
  return username.trim();
}

function slugifyPart(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "")
    .trim();
}

function normalizeFullName(fullName: string) {
  return fullName
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => {
      const [first = "", ...rest] = part;
      return first.toLocaleUpperCase() + rest.join("").toLocaleLowerCase();
    })
    .join(" ");
}

function normalizeRecoveryKey(key: string) {
  return key.trim().toUpperCase().replace(/\s+/g, "");
}

function buildAccountUsername(fullName: string, email: string) {
  const nameBase = normalizeFullName(fullName)
    .split(" ")
    .map(slugifyPart)
    .join("");

  const emailBase = slugifyPart(email.split("@")[0] || "");
  return nameBase || emailBase || "account";
}

function generateUniqueUsername(users: StoredUserRecord[], fullName: string, email: string) {
  const base = buildAccountUsername(fullName, email);
  let candidate = base;
  let counter = 2;

  while (users.some((user) => user.username === candidate)) {
    candidate = `${base}${counter}`;
    counter += 1;
  }

  return candidate;
}

function publicUserFromRecord(user: StoredUserRecord): User {
  return {
    fullName: normalizeFullName(user.fullName),
    email: user.email,
    username: user.username,
  };
}

function getAllUsers(): StoredUserRecord[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveAllUsers(users: StoredUserRecord[]) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

function ensureSeedUsersSync() {
  if (typeof window === "undefined") return;
  const users = getAllUsers();
  const devIndex = users.findIndex((user) => user.username === DEV_USER.username);
  if (devIndex === -1) {
    users.push(DEV_USER);
    saveAllUsers(users);
    return;
  }

  const dev = users[devIndex];
  const nextDev = {
    ...dev,
    ...DEV_USER,
  };
  users[devIndex] = nextDev;
  saveAllUsers(users);
}

async function hashValue(value: string) {
  const encoded = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", encoded);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

async function migrateLegacyUsers() {
  if (typeof window === "undefined") return;
  const users = getAllUsers();
  let changed = false;

  for (const user of users) {
    const normalizedFullName = normalizeFullName(user.fullName);
    if (normalizedFullName !== user.fullName) {
      user.fullName = normalizedFullName;
      changed = true;
    }

    if (!user.passwordHash && user.password) {
      user.passwordHash = await hashValue(user.password);
      delete user.password;
      changed = true;
    }

    if (!user.recoveryKeyHash && user.recoveryKey) {
      user.recoveryKeyHash = await hashValue(normalizeRecoveryKey(user.recoveryKey));
      delete user.recoveryKey;
      changed = true;
    }
  }

  if (changed) {
    saveAllUsers(users);
  }
}

async function ensureAuthData() {
  ensureSeedUsersSync();
  await migrateLegacyUsers();
}

function generateRecoveryKey() {
  const bytes = crypto.getRandomValues(new Uint8Array(20));
  const parts = ["PLAB"];
  for (let groupIndex = 0; groupIndex < 5; groupIndex += 1) {
    let part = "";
    for (let i = 0; i < 4; i += 1) {
      part += RECOVERY_KEY_ALPHABET[bytes[groupIndex * 4 + i] % RECOVERY_KEY_ALPHABET.length];
    }
    parts.push(part);
  }
  return parts.join("-");
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  ensureSeedUsersSync();
  const data = localStorage.getItem(USER_KEY);
  if (!data) return null;
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export function getRememberedUser(): string | null {
  if (typeof window === "undefined") return null;
  ensureSeedUsersSync();
  return localStorage.getItem(REMEMBERED_USER_KEY);
}

export function getRememberMeEnabled(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(REMEMBER_ME_KEY) === "true";
}

export function listLocalProfiles(): User[] {
  if (typeof window === "undefined") return [];
  ensureSeedUsersSync();
  return getAllUsers()
    .map(publicUserFromRecord)
    .sort((a, b) => a.username.localeCompare(b.username));
}

export async function updateLocalProfile({
  currentUsername,
  fullName,
  email,
  username,
  nextPassword,
}: {
  currentUsername: string;
  fullName: string;
  email: string;
  username: string;
  nextPassword?: string;
}) {
  await ensureAuthData();
  const users = getAllUsers();
  const normalizedCurrentUsername = normalizeUsername(currentUsername);
  const normalizedNextUsername = normalizeUsername(username);
  const found = users.find((user) => user.username === normalizedCurrentUsername);
  if (!found) {
    throw new Error("Profile not found");
  }

  if (
    normalizedNextUsername !== normalizedCurrentUsername &&
    users.some((user) => user.username === normalizedNextUsername)
  ) {
    throw new Error("Username already exists");
  }

  found.fullName = normalizeFullName(fullName);
  found.email = email.trim();
  found.username = normalizedNextUsername;

  if (nextPassword?.trim()) {
    found.passwordHash = await hashValue(nextPassword);
    delete found.password;
  }

  saveAllUsers(users);

  const remembered = localStorage.getItem(REMEMBERED_USER_KEY);
  if (remembered === normalizedCurrentUsername) {
    localStorage.setItem(REMEMBERED_USER_KEY, normalizedNextUsername);
  }

  const stored = getStoredUser();
  if (stored?.username === normalizedCurrentUsername) {
    localStorage.setItem(
      USER_KEY,
      JSON.stringify({
        fullName: found.fullName,
        email: found.email,
        username: found.username,
      }),
    );
  }
}

export async function deleteLocalProfile(username: string) {
  await ensureAuthData();
  const normalizedUsername = normalizeUsername(username);
  const users = getAllUsers();
  const nextUsers = users.filter((user) => user.username !== normalizedUsername);
  saveAllUsers(nextUsers);

  if (localStorage.getItem(REMEMBERED_USER_KEY) === normalizedUsername) {
    localStorage.removeItem(REMEMBERED_USER_KEY);
    localStorage.removeItem(REMEMBER_ME_KEY);
  }

  const stored = getStoredUser();
  if (stored?.username === normalizedUsername) {
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(SESSION_KEY);
  }
}

export function setStoredUser(user: User, remember: boolean) {
  ensureSeedUsersSync();
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  localStorage.setItem(SESSION_KEY, "active");
  if (remember) {
    localStorage.setItem(REMEMBERED_USER_KEY, user.username);
    localStorage.setItem(REMEMBER_ME_KEY, "true");
  } else {
    localStorage.removeItem(REMEMBERED_USER_KEY);
    localStorage.removeItem(REMEMBER_ME_KEY);
  }
}

export function touchActiveSession() {
  // Session lifetime is currently explicit and logout-driven.
  // This remains as a compatibility no-op while the frontend is browser-only.
}

export function clearActiveSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(SESSION_KEY);
}

export function hasActiveSession(): boolean {
  if (typeof window === "undefined") return false;
  ensureSeedUsersSync();

  const sessionState = localStorage.getItem(SESSION_KEY);
  const storedUser = localStorage.getItem(USER_KEY);

  if (sessionState !== "active" || !storedUser) {
    clearActiveSession();
    return false;
  }

  return true;
}

export async function registerUser(user: Omit<User, "username"> & { password: string }) {
  await ensureAuthData();
  const users = getAllUsers();
  const username = generateUniqueUsername(users, user.fullName, user.email);

  const recoveryKey = generateRecoveryKey();
  users.push({
    fullName: normalizeFullName(user.fullName),
    email: user.email.trim(),
    username,
    passwordHash: await hashValue(user.password),
    recoveryKeyHash: await hashValue(normalizeRecoveryKey(recoveryKey)),
  });
  saveAllUsers(users);

  return {
    user: {
      fullName: normalizeFullName(user.fullName),
      email: user.email.trim(),
      username,
    },
    recoveryKey,
  };
}

export async function loginUser(username: string, password: string): Promise<User | null> {
  await ensureAuthData();
  const normalizedUsername = normalizeUsername(username);
  const users = getAllUsers();
  const found = users.find((user) => user.username === normalizedUsername);
  if (!found) return null;

  if (found.passwordHash) {
    const incomingHash = await hashValue(password);
    if (incomingHash !== found.passwordHash) return null;
    return publicUserFromRecord(found);
  }

  if (found.password && found.password === password) {
    found.passwordHash = await hashValue(password);
    delete found.password;
    saveAllUsers(users);
    return publicUserFromRecord(found);
  }

  return null;
}

export async function recoverAccess({
  username,
  recoveryKey,
  newPassword,
}: {
  username: string;
  recoveryKey: string;
  newPassword: string;
}) {
  await ensureAuthData();
  const normalizedUsername = normalizeUsername(username);
  const users = getAllUsers();
  const found = users.find((user) => user.username === normalizedUsername);
  if (!found || !found.recoveryKeyHash) {
    return null;
  }

  const incomingRecoveryHash = await hashValue(normalizeRecoveryKey(recoveryKey));
  if (incomingRecoveryHash !== found.recoveryKeyHash) {
    return null;
  }

  const nextPasswordHash = await hashValue(newPassword);
  const matchesCurrentPassword =
    (found.passwordHash && nextPasswordHash === found.passwordHash) ||
    (!!found.password && found.password === newPassword);

  if (matchesCurrentPassword) {
    throw new Error("Choose a new password that is different from your current password");
  }

  const nextRecoveryKey = generateRecoveryKey();
  found.passwordHash = nextPasswordHash;
  found.recoveryKeyHash = await hashValue(normalizeRecoveryKey(nextRecoveryKey));
  delete found.password;
  delete found.recoveryKey;
  saveAllUsers(users);

  return {
    user: publicUserFromRecord(found),
    recoveryKey: nextRecoveryKey,
  };
}

export function logout() {
  clearActiveSession();
  localStorage.removeItem(REMEMBERED_USER_KEY);
  localStorage.removeItem(REMEMBER_ME_KEY);
}

export function isLoggedIn(): boolean {
  return hasActiveSession();
}
