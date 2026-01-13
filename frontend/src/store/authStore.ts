import { create } from 'zustand';
import { authService, UserResponse } from '../services/auth.service';
import { useToastStore } from './toastStore';

interface AuthState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: authService.isAuthenticated(),
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      await authService.login(email, password);
      const user = await authService.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
      useToastStore.getState().success('로그인 성공!');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '로그인에 실패했습니다';
      set({ isLoading: false, isAuthenticated: false });
      useToastStore.getState().error(errorMessage);
      throw error;
    }
  },

  register: async (email: string, username: string, password: string, fullName?: string) => {
    set({ isLoading: true });
    try {
      await authService.register({
        email,
        username,
        password,
        full_name: fullName,
      });
      // Auto login after registration
      await authService.login(email, password);
      const user = await authService.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
      useToastStore.getState().success('회원가입 성공!');
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '회원가입에 실패했습니다';
      set({ isLoading: false });
      useToastStore.getState().error(errorMessage);
      throw error;
    }
  },

  logout: () => {
    authService.logout();
    set({ user: null, isAuthenticated: false });
    useToastStore.getState().info('로그아웃되었습니다');
  },

  loadUser: async () => {
    if (!authService.isAuthenticated()) {
      set({ user: null, isAuthenticated: false });
      return;
    }

    set({ isLoading: true });
    try {
      const user = await authService.getCurrentUser();
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      // Token is invalid, clear auth state
      authService.logout();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
}));

export default useAuthStore;
