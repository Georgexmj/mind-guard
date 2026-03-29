import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      setAuth: (user: User, token: string) => {
        localStorage.setItem('access_token', token)
        set({ user, token })
      },
      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, token: null })
      },
      isAuthenticated: () => {
        const state = get()
        return state.token !== null && state.user !== null
      },
    }),
    {
      name: 'cognicare-auth',
      partialize: (state) => ({ user: state.user, token: state.token }),
    }
  )
)
