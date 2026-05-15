<template>
  <div class="app-wrapper">
    <AppSidebar
      :active-nav="activeNav"
      :current-user="currentUser"
      :is-admin="isAdmin"
      :is-authenticated="isAuthenticated"
      @new-chat="handleNewChat"
      @history="handleHistory"
      @settings="handleSettings"
      @clear-chat="handleClearChat"
      @logout="handleLogout"
    />

    <main class="main-content">
      <AuthPanel
        v-if="!isAuthenticated"
        :form="authForm"
        :loading="authLoading"
        :mode="authMode"
        @submit="handleAuthSubmit"
        @switch-mode="toggleAuthMode"
      />

      <DocumentManager
        v-else-if="activeNav === 'settings'"
        :documents="documents"
        :loading="documentsLoading"
        :selected-files="selectedFiles"
        :uploading="isUploading"
        :upload-progress="uploadProgress"
        :upload-percent="uploadPercent"
        @select-files="handleFileSelect"
        @upload-files="uploadDocument"
        @refresh="loadDocuments"
        @delete-document="deleteDocument"
      />

      <HistorySidebar
        v-if="isAuthenticated && showHistorySidebar"
        :active-session-id="sessionId"
        :sessions="sessions"
        @close="showHistorySidebar = false"
        @load-session="loadSession"
        @delete-session="deleteSession"
      />

      <div v-show="isAuthenticated && activeNav !== 'settings'" class="chat-area">
        <header class="chat-header">
          <div class="header-info">
            <div class="status-dot"></div>
            <span>知识源在线中...</span>
          </div>
          <div class="header-actions">
            <button
              class="icon-btn theme-toggle-btn"
              :title="isDarkMode ? '切换到日间模式' : '切换到夜间模式'"
              @click="toggleTheme"
            >
              <i :class="isDarkMode ? 'fas fa-sun' : 'fas fa-moon'"></i>
            </button>
            <button class="icon-btn" title="更多"><i class="fas fa-ellipsis-h"></i></button>
          </div>
        </header>

        <MessageList :messages="messages" />

        <MessageInput
          v-model="userInput"
          :loading="isLoading"
          @send="handleSend"
          @stop="handleStop"
        />
      </div>
    </main>
  </div>
</template>

<script>
import { config } from '../config';
import { createInitialState } from '../state';
import { createApiService } from '../services/api';
import { configureMarkdown } from '../services/markdown';
import AppSidebar from '../components/layout/AppSidebar.vue';
import AuthPanel from '../components/auth/AuthPanel.vue';
import DocumentManager from '../components/documents/DocumentManager.vue';
import HistorySidebar from '../components/history/HistorySidebar.vue';
import MessageInput from '../components/chat/MessageInput.vue';
import MessageList from '../components/chat/MessageList.vue';
import { authMethods } from './workspace/authMethods';
import { chatMethods } from './workspace/chatMethods';
import { documentMethods } from './workspace/documentMethods';
import { sessionMethods } from './workspace/sessionMethods';
import { uiMethods } from './workspace/uiMethods';

export default {
  components: {
    AppSidebar,
    AuthPanel,
    DocumentManager,
    HistorySidebar,
    MessageInput,
    MessageList
  },
  data() {
    return {
      ...createInitialState(config),
      api: null
    };
  },
  computed: {
    isAuthenticated() {
      return !!this.token && !!this.currentUser;
    },
    isAdmin() {
      return this.currentUser?.role === 'admin';
    }
  },
  async mounted() {
    configureMarkdown();
    this.api = createApiService(config.BASE_URL);
    this.applyTheme();
    await this.restoreAuth();
  },
  methods: {
    ...authMethods,
    ...uiMethods,
    ...chatMethods,
    ...sessionMethods,
    ...documentMethods
  }
};
</script>
