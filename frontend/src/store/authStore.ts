import { create } from 'zustand';

interface User {
  user_id: string;
  email: string;
  name: string;
  role: string;
  org_id?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: sessionStorage.getItem('shelfiq_token'),
  isAuthenticated: !!sessionStorage.getItem('shelfiq_token'),
  login: (token, user) => {
    sessionStorage.setItem('shelfiq_token', token);
    set({ token, user, isAuthenticated: true });
  },
  logout: () => {
    sessionStorage.removeItem('shelfiq_token');
    set({ token: null, user: null, isAuthenticated: false });
  },
}));
