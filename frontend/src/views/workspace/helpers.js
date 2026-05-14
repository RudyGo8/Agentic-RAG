export function createSessionId() {
  return `session_${Date.now()}`;
}

export function createAssistantMessage() {
  return {
    text: '',
    isUser: false,
    isThinking: true,
    ragTrace: null,
    ragSteps: [],
    showTrace: false
  };
}

export function appendUniqueRagStep(message, step) {
  if (!message || !Array.isArray(message.ragSteps) || !step) return;

  const icon = step.icon || '';
  const label = step.label || '';
  const detail = step.detail || '';
  const signature = `${icon}|${label}|${detail}`;
  const last = message.ragSteps.at(-1);
  const lastSignature = last ? `${last.icon || ''}|${last.label || ''}|${last.detail || ''}` : '';

  if (signature !== lastSignature) {
    message.ragSteps.push(step);
  }
}

export function normalizeSessionMessages(messages = []) {
  return messages.map((msg) => ({
    text: msg.content,
    isUser: msg.type === 'human',
    ragTrace: msg.rag_trace || null,
    ragSteps: [],
    showTrace: false
  }));
}

export function buildUploadProgressMessage(data) {
  const failedItems = Array.isArray(data?.results)
    ? data.results.filter((item) => item && item.success === false)
    : [];

  if (!failedItems.length) {
    return data?.message || '';
  }

  const details = failedItems
    .map((item) => `${item.filename}: ${item.message || 'Upload failed'}`)
    .join('；');

  return `${data.message}。失败详情：${details}`;
}
