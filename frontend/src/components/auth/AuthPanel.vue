<template>
  <div class="auth-panel">
    <div class="auth-hero">
      <span class="auth-chip">Agentic RAG Workspace</span>
      <h2>{{ mode === 'login' ? '登录知源' : '注册知源' }}</h2>
      <p>登录后可使用流式问答、会话历史和文档知识库能力。</p>
    </div>

    <div class="auth-mode-tabs">
      <button
        type="button"
        class="auth-mode-tab"
        :class="{ active: mode === 'login' }"
        :disabled="mode === 'login'"
        @click="$emit('switch-mode')"
      >
        登录
      </button>
      <button
        type="button"
        class="auth-mode-tab"
        :class="{ active: mode === 'register' }"
        :disabled="mode === 'register'"
        @click="$emit('switch-mode')"
      >
        注册
      </button>
    </div>

    <div class="auth-form">
      <label class="auth-field">
        <span>用户名</span>
        <input v-model="form.username" type="text" placeholder="请输入用户名" />
      </label>

      <label class="auth-field">
        <span>密码</span>
        <input v-model="form.password" type="password" placeholder="请输入密码" />
      </label>

      <label v-if="mode === 'register'" class="auth-field">
        <span>账号类型</span>
        <select v-model="form.role">
          <option value="user">普通用户</option>
          <option value="admin">管理员</option>
        </select>
      </label>

      <label v-if="mode === 'register' && form.role === 'admin'" class="auth-field">
        <span>管理员邀请码</span>
        <input
          v-model="form.admin_code"
          type="password"
          placeholder="请输入管理员邀请码"
        />
      </label>

      <button type="button" class="send-btn auth-submit" :disabled="loading" @click="$emit('submit')">
        <i class="fas" :class="mode === 'login' ? 'fa-right-to-bracket' : 'fa-user-plus'"></i>
        {{ loading ? '提交中...' : (mode === 'login' ? '登录' : '注册') }}
      </button>

      <button type="button" class="auth-switch" @click="$emit('switch-mode')">
        {{ mode === 'login' ? '没有账号？去注册' : '已有账号？去登录' }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    form: {
      type: Object,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    },
    mode: {
      type: String,
      required: true
    }
  },
  emits: ['submit', 'switch-mode']
};
</script>
