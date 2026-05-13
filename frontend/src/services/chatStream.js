export async function consumeChatStream(response, handlers = {}) {
  // 后端返回的是 text/event-stream；这里直接读取 Response.body 持续消费流。
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    let eventEndIndex = buffer.indexOf('\n\n');

    while (eventEndIndex !== -1) {
      // SSE 每个事件之间用空行分隔，这里手动把一个完整事件从 buffer 中切出来。
      const eventStr = buffer.slice(0, eventEndIndex);
      buffer = buffer.slice(eventEndIndex + 2);
      eventEndIndex = buffer.indexOf('\n\n');

      if (!eventStr.startsWith('data: ')) continue;

      const dataStr = eventStr.slice(6);
      if (dataStr === '[DONE]') {
        handlers.onDone?.();
        continue;
      }

      try {
        const data = JSON.parse(dataStr);
        if (data.type === 'content') {
          // AI 正文增量。
          handlers.onContent?.(data.content || '');
        } else if (data.type === 'trace') {
          // 本轮最终 trace，通常在流结束前统一返回一次。
          handlers.onTrace?.(data.rag_trace || null);
        } else if (data.type === 'rag_step') {
          // RAG 中间步骤，用于展示“正在检索/改写/重排”等过程。
          handlers.onRagStep?.(data.step || null);
        } else if (data.type === 'error') {
          handlers.onError?.(data.error || data.content || 'Unknown error');
        }
      } catch (error) {
        handlers.onParseError?.(error, dataStr);
      }
    }

    handlers.onChunk?.();
  }
}
