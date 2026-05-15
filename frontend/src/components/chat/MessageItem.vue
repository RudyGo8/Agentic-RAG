<template>
  <div :class="['message', message.isUser ? 'user-message' : 'bot-message']">
    <div v-if="showThinking" class="message-content thinking-content">
      <div class="thinking-header">
        <div class="thinking-dots">
          <span class="tdot"></span>
          <span class="tdot"></span>
          <span class="tdot"></span>
        </div>
        <span v-if="!message.ragSteps || !message.ragSteps.length" class="thinking-text">正在思考中...</span>
        <span v-else class="thinking-text">{{ message.ragSteps[message.ragSteps.length - 1].label }}</span>
      </div>
    </div>

    <div v-if="showTraceLines" class="thinking-trace-lines">
      <div v-for="(step, index) in message.ragSteps" :key="index" class="thinking-trace-line">
        <span class="thinking-trace-icon">{{ step.icon || '•' }}</span>
        <span class="thinking-trace-label">{{ step.label }}</span>
        <span v-if="step.detail" class="thinking-trace-detail">{{ step.detail }}</span>
      </div>
    </div>

    <div class="message-content" v-html="renderedContent"></div>

    <ChartDisplay v-if="!message.isUser && hasChartJson" :content="message.text" />

    <div v-if="!message.isUser && message.ragTrace" class="message-meta">
      <button class="trace-btn" @click="toggleTrace">
        检索过程
      </button>

      <div v-if="message.showTrace" class="trace-panel">
        <div class="trace-meta">
          <div>检索模式：{{ message.ragTrace.retrieval_mode || '-' }}</div>
          <div>候选召回数：{{ message.ragTrace.candidate_k || '-' }}</div>
          <div>叶子召回层级：{{ message.ragTrace.leaf_retrieve_level || '-' }}</div>
          <div>Auto-merging启用：{{ message.ragTrace.auto_merge_enabled ? '是' : '否' }}</div>
          <div>Auto-merging应用：{{ message.ragTrace.auto_merge_applied ? '是' : '否' }}</div>
          <div>合并阈值：{{ message.ragTrace.auto_merge_threshold || '-' }}</div>
          <div>合并替换片段：{{ message.ragTrace.auto_merge_replaced_chunks || 0 }}</div>
          <div>合并轮次：{{ message.ragTrace.auto_merge_steps || 0 }}</div>
          <div>Rerank已配置：{{ message.ragTrace.rerank_enabled ? '是' : '否' }}</div>
          <div>Rerank已执行：{{ message.ragTrace.rerank_applied ? '是' : '否' }}</div>
          <div>Rerank模型：{{ message.ragTrace.rerank_model || '-' }}</div>
          <div>扩展查询：{{ message.ragTrace.query || '-' }}</div>
        </div>

        <h3 class="trace-title">初次检索结果</h3>

        <div
          v-for="(chunk, index) in chunksToRender"
          :key="chunk.chunk_id || chunk.id || `${index}-${chunk.filename || chunk.file_name || ''}`"
          class="trace-chunk"
        >
          <div class="chunk-title">
            {{ chunk.filename || chunk.file_name || '未知文件' }}
            <span v-if="(chunk.page_number || chunk.page)">（第 {{ chunk.page_number || chunk.page }} 页）</span>
          </div>

          <div class="chunk-score">
            RRF名次：#{{ chunk.rrf_rank || chunk.rank || chunk.final_rank || (index + 1) }}
            <span v-if="chunk.rerank_score !== undefined && chunk.rerank_score !== null">
              ｜Rerank分数：{{ Number(chunk.rerank_score).toFixed(4) }}
            </span>
          </div>

          <div class="chunk-text">
            {{ chunk.text || '-' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { escapeHtml, renderMarkdown } from '../../services/markdown'
import ChartDisplay from './ChartDisplay.vue'

export default {
  components: { ChartDisplay },
  props: {
    message: {
      type: Object,
      required: true
    }
  },
  computed: {
    showThinking() {
      return !this.message.isUser && this.message.isThinking && !this.message.text;
    },
    hasChartJson() {
      try {
        let t = this.message.text || ''
        // 先试从 markdown code block 里提取
        const code = t.match(/```(?:json)?\s*([\s\S]*?)```/)
        if (code) t = code[1]
        const m = t.match(/\{[\s\S]*"chart"[\s\S]*\}/)
        if (!m) return false
        const p = JSON.parse(m[0])
        return !!(p.chart && p.data)
      } catch { return false }
    },
    showTraceLines() {
      return !this.message.isUser
        && Array.isArray(this.message.ragSteps)
        && this.message.ragSteps.length > 0;
    },
    renderedContent() {
      if (this.message.isUser) return escapeHtml(this.message.text)
      // bot 消息：摘掉 chart JSON 块，只显示分析文本
      let text = (this.message.text || '').replace(/\{[\s\S]*"chart"[\s\S]*\}/, '').trim()
      return renderMarkdown(text)
    },
    chunksToRender() {
      const trace = this.message.ragTrace || {};
      // 兼容不同阶段写入的 trace 字段，优先展示最终 retrieved_chunks。
      if (Array.isArray(trace.retrieved_chunks) && trace.retrieved_chunks.length) return trace.retrieved_chunks;
      if (Array.isArray(trace.initial_retrieved_chunks) && trace.initial_retrieved_chunks.length) return trace.initial_retrieved_chunks;
      if (Array.isArray(trace.expanded_retrieved_chunks) && trace.expanded_retrieved_chunks.length) return trace.expanded_retrieved_chunks;
      return [];
    }
  },
  methods: {
    toggleTrace() {
      this.message.showTrace = !this.message.showTrace;
    }
  }
};
</script>
