import { create } from "zustand";
import { fetchCurrentUser, login as loginRequest, type AuthUser } from "@/lib/api/endpoints";

type AuthStatus = "idle" | "loading" | "authenticated" | "unauthenticated";

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  status: AuthStatus;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  /** Sayfa ilk açıldığında localStorage'daki token'ı doğrular ve kullanıcıyı yükler. */
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("access_token"),
  user: null,
  status: "idle",

  async login(username, password) {
    const token = await loginRequest(username, password);
    localStorage.setItem("access_token", token);
    set({ token });
    const user = await fetchCurrentUser();
    set({ user, status: "authenticated" });
  },

  logout() {
    localStorage.removeItem("access_token");
    set({ token: null, user: null, status: "unauthenticated" });
  },

  async hydrate() {
    const token = localStorage.getItem("access_token");
    if (!token) {
      set({ status: "unauthenticated" });
      return;
    }
    set({ status: "loading", token });
    try {
      const user = await fetchCurrentUser();
      set({ user, status: "authenticated" });
    } catch {
      localStorage.removeItem("access_token");
      set({ token: null, user: null, status: "unauthenticated" });
    }
  },
}));
