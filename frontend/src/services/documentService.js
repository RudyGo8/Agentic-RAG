export async function listDocuments(api, token) {
  const { response, data } = await api.requestJson('/documents', { token });
  if (!response.ok) {
    const error = new Error(data.detail || 'Failed to load documents');
    error.status = response.status;
    throw error;
  }
  return data.documents || [];
}

export function uploadDocumentFiles(api, token, files, onProgress) {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${api.baseUrl}/documents/batch-upload`);

    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        const percent = Math.round((e.loaded / e.total) * 100);
        onProgress(percent);
      }
    });

    xhr.addEventListener('load', () => {
      let data = {};
      try {
        data = JSON.parse(xhr.responseText);
      } catch (_) { /* ignore */ }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data);
      } else {
        const error = new Error(data.detail || 'Batch upload failed');
        error.status = xhr.status;
        reject(error);
      }
    });

    xhr.addEventListener('error', () => {
      reject(new Error('网络错误，上传失败'));
    });

    xhr.addEventListener('abort', () => {
      reject(new Error('上传已取消'));
    });

    xhr.send(formData);
  });
}


export async function removeDocument(api, token, filename) {
  const { response, data } = await api.requestJson(`/documents/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
    token
  });
  if (!response.ok) {
    const error = new Error(data.detail || 'Delete failed');
    error.status = response.status;
    throw error;
  }
  return data;
}
