import { getSessionMessages, listSessions, removeSession } from '../../services/sessionService';
import { createSessionId, normalizeSessionMessages } from './helpers';

export const sessionMethods = {
  handleNewChat() {
    if (!this.isAuthenticated) return;

    this.messages = [];
    this.sessionId = createSessionId();
    this.activeNav = 'newChat';
    this.showHistorySidebar = false;
  },
  handleClearChat() {
    if (confirm('确定要清空当前对话吗？')) {
      this.messages = [];
    }
  },
  async handleHistory() {
    if (!this.isAuthenticated) return;

    this.activeNav = 'history';
    this.showHistorySidebar = true;

    try {
      this.sessions = await listSessions(this.api, this.token);
    } catch (error) {
      alert(`加载历史记录失败：${this.handleServiceError(error)}`);
    }
  },
  async loadSession(sessionId) {
    this.sessionId = sessionId;
    this.showHistorySidebar = false;
    this.activeNav = 'newChat';

    try {
      const messages = await getSessionMessages(this.api, this.token, sessionId);
      this.messages = normalizeSessionMessages(messages);
    } catch (error) {
      alert(`加载会话失败：${this.handleServiceError(error)}`);
      this.messages = [];
    }
  },
  async deleteSession(sessionId) {
    if (!confirm(`确定要删除会话 "${sessionId}" 吗？`)) return;

    try {
      const payload = await removeSession(this.api, this.token, sessionId);
      this.sessions = this.sessions.filter((item) => item.session_id !== sessionId);

      if (this.sessionId === sessionId) {
        this.messages = [];
        this.sessionId = createSessionId();
        this.activeNav = 'newChat';
      }

      if (payload.message) alert(payload.message);
    } catch (error) {
      alert(`删除会话失败：${this.handleServiceError(error)}`);
    }
  }
};
