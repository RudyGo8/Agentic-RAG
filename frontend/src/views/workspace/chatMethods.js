import { openChatStream } from '../../services/chatService';
import { consumeChatStream } from '../../services/chatStream';
import { appendUniqueRagStep, createAssistantMessage } from './helpers';

export const chatMethods = {
  handleStop() {
    this.abortController?.abort();
  },
  appendRagStep(message, step) {
    appendUniqueRagStep(message, step);
  },
  async handleSend() {
    if (!this.isAuthenticated) {
      alert('请先登录');
      return;
    }

    const text = this.userInput.trim();
    if (!text || this.isLoading) return;

    this.messages.push({ text, isUser: true });
    this.userInput = '';
    this.isLoading = true;

    this.messages.push(createAssistantMessage());
    const botMsg = this.messages[this.messages.length - 1];
    this.abortController = new AbortController();
    
    // SSE 入口
    try {
      const response = await openChatStream(this.api, this.token, {
        message: text,
        sessionId: this.sessionId,
        signal: this.abortController.signal
      });

      if (!response.ok) {
        if (response.status === 401) this.handleLogout();
        throw new Error(`HTTP ${response.status}`);
      }

      await consumeChatStream(response, {
        onContent: (content) => {
          botMsg.isThinking = false;
          botMsg.text += content;
        },
        onTrace: (ragTrace) => {
          botMsg.ragTrace = ragTrace;
        },
        onRagStep: (step) => {
          this.appendRagStep(botMsg, step);
        },
        onError: (errorMsg) => {
          botMsg.isThinking = false;
          botMsg.text += `\n[Error: ${errorMsg}]`;
        },
        onDone: () => {
          botMsg.isThinking = false;
        },
        onParseError: (error) => {
          console.warn('SSE parse error:', error);
        }
      });
    } catch (error) {
      botMsg.isThinking = false;
      if (error.name === 'AbortError') {
        botMsg.text = botMsg.text
          ? `${botMsg.text}\n\n_(回答已被终止)_`
          : '(已终止回答)';
      } else {
        botMsg.text = `Sorry... 出了点问题：${error.message}`;
      }
    } finally {
      this.isLoading = false;
      this.abortController = null;
    }
  }
};
