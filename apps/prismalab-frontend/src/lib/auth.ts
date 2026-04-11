export interface User {
  fullName: string;
  email: string;
  username: string;
}

interface StoredUserRecord extends User {
  password: string;
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
  password: "luis22021989",
};

function ensureSeedUsers() {
  if (typeof window === "undefined") return;
  const users = getAllUsers();
  const exists = users.some((user) => user.username === DEV_USER.username);
  if (!exists) {
    users.push(DEV_USER);
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  }
}

function getAllUsers(): StoredUserRecord[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY) || "[]");
  } catch {
    return [];
  }
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  ensureSeedUsers();
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
  ensureSeedUsers();
  return localStorage.getItem(REMEMBERED_USER_KEY);
}

export function setStoredUser(user: User, remember: boolean) {
  ensureSeedUsers();
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

export function registerUser(user: User & { password: string }) {
  ensureSeedUsers();
  const users = getAllUsers();
  if (users.some((existing) => existing.username === user.username)) {
    throw new Error("Username already exists");
  }
  users.push(user);
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

export function loginUser(username: string, password: string): User | null {
  ensureSeedUsers();
  const users = getAllUsers();
  const found = users.find((u) => u.username === username && u.password === password);
  if (!found) return null;
  return { fullName: found.fullName, email: found.email, username: found.username };
}

export function logout() {
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(REMEMBERED_USER_KEY);
  localStorage.removeItem(REMEMBER_ME_KEY);
}

export function isLoggedIn(): boolean {
  if (typeof window === "undefined") return false;
  ensureSeedUsers();
  return localStorage.getItem(SESSION_KEY) === "active";
}
