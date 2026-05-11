import { create } from "zustand";
import { User } from "@/types";
import api from "@/lib/api";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
}

interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  org_name: string;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,

  login: async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("access_token", data.access_token);
    const me = await api.get("/auth/me");
    set({ user: me.data });
  },

  register: async (registerData) => {
    const { data } = await api.post("/auth/register", registerData);
    localStorage.setItem("access_token", data.access_token);
    const me = await api.get("/auth/me");
    set({ user: me.data });
  },

  logout: async () => {
    await api.post("/auth/logout");
    localStorage.removeItem("access_token");
    set({ user: null });
  },

  fetchMe: async () => {
    set({ isLoading: true });
    try {
      const { data } = await api.get("/auth/me");
      set({ user: data });
    } catch {
      localStorage.removeItem("access_token");
    } finally {
      set({ isLoading: false });
    }
  },
}));