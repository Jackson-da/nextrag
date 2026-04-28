import request from './request'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface RegisterResponse {
  message: string
  user_id: string
}

export interface UserInfo {
  id: string
  username: string
}

export const authApi = {
  // 注册
  register(data: RegisterRequest): Promise<RegisterResponse> {
    return request.post<RegisterResponse>('/auth/register', data)
  },

  // 登录
  login(data: LoginRequest): Promise<LoginResponse> {
    return request.post<LoginResponse>('/auth/login', data)
  },

  // 获取当前用户信息
  getCurrentUser(): Promise<UserInfo> {
    return request.get<UserInfo>('/auth/me')
  },
}

// Token 管理
export const tokenManager = {
  // 获取 Token
  getToken(): string | null {
    return localStorage.getItem('token')
  },

  // 设置 Token
  setToken(token: string): void {
    localStorage.setItem('token', token)
  },

  // 清除 Token
  removeToken(): void {
    localStorage.removeItem('token')
  },

  // 检查是否已登录
  isLoggedIn(): boolean {
    return !!this.getToken()
  },
}
