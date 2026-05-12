import type { User } from '../types'

// 最简单的认证服务
export const authService = {
  getUser(): User | null {
    try {
      const stored = localStorage.getItem('mindguard-user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  },

  getToken(): string | null {
    return localStorage.getItem('access_token')
  },

  setAuth(user: User, token: string): void {
    localStorage.setItem('mindguard-user', JSON.stringify(user))
    localStorage.setItem('access_token', token)
  },

  logout(): void {
    localStorage.removeItem('mindguard-user')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  isAuthenticated(): boolean {
    return this.getToken() !== null && this.getUser() !== null
  },
}

// 保持兼容性的 hook
export const useAuthStore = () => ({
  user: authService.getUser(),
  token: authService.getToken(),
  setAuth: authService.setAuth.bind(authService),
  logout: authService.logout.bind(authService),
  isAuthenticated: authService.isAuthenticated.bind(authService),
})
