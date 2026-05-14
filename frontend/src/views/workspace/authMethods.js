import { config } from '../../config';
import { fetchCurrentUser, login as loginUser, register as registerUser } from '../../services/authService';
import { createSessionId } from './helpers';

export const authMethods = {
  async restoreAuth() {
    if (!this.token) return;

    try {
      await this.fetchMe();
    } catch (_) {
      this.handleLogout();
    }
  },
  handleServiceError(error) {
    if (error?.status === 401) {
      this.handleLogout();
    }
    return error?.message || '请求失败';
  },
  toggleAuthMode() {
    this.authMode = this.authMode === 'login' ? 'register' : 'login';
  },
  async fetchMe() {
    this.currentUser = await fetchCurrentUser(this.api, this.token);
  },
  async handleAuthSubmit() {
    if (this.authLoading) return;

    const username = this.authForm.username.trim();
    const password = this.authForm.password.trim();
    if (!username || !password) {
      alert('用户名和密码不能为空');
      return;
    }

    this.authLoading = true;
    try {
      const payload = { username, password };
      const data = this.authMode === 'register'
        ? await registerUser(this.api, {
          ...payload,
          role: this.authForm.role,
          admin_code: this.authForm.admin_code || null
        })
        : await loginUser(this.api, payload);

      this.token = data.access_token;
      this.currentUser = { username: data.username, role: data.role };
      this.messages = [];
      this.sessionId = createSessionId();
      this.activeNav = 'newChat';
      this.showHistorySidebar = false;

      this.authForm.password = '';
      this.authForm.admin_code = '';

      localStorage.setItem(config.TOKEN_STORAGE_KEY, this.token);
    } catch (error) {
      alert(this.handleServiceError(error));
    } finally {
      this.authLoading = false;
    }
  },
  handleLogout() {
    this.abortController?.abort();
    this.abortController = null;

    this.token = '';
    this.currentUser = null;
    this.messages = [];
    this.sessions = [];
    this.documents = [];
    this.selectedFiles = [];
    this.uploadProgress = '';
    this.isLoading = false;
    this.activeNav = 'newChat';
    this.showHistorySidebar = false;

    localStorage.removeItem(config.TOKEN_STORAGE_KEY);
  }
};
