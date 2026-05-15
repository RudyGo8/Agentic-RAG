import { listDocuments, removeDocument, uploadDocumentFiles } from '../../services/documentService';
import { buildUploadProgressMessage } from './helpers';

export const documentMethods = {
  handleFileSelect(files) {
    this.selectedFiles = Array.isArray(files) ? files : [];
    this.uploadProgress = '';
    this.uploadPercent = 0;
  },
  async loadDocuments() {
    this.documentsLoading = true;
    try {
      this.documents = await listDocuments(this.api, this.token);
    } catch (error) {
      alert(`加载文档列表失败：${this.handleServiceError(error)}`);
    } finally {
      this.documentsLoading = false;
    }
  },
  async uploadDocument() {
    if (!this.selectedFiles.length) {
      alert('请先选择文件');
      return;
    }

    this.isUploading = true;
    this.uploadPercent = 0;
    this.uploadProgress = '正在上传...';

    try {
      const data = await uploadDocumentFiles(
        this.api,
        this.token,
        this.selectedFiles,
        (percent) => {
          this.uploadPercent = percent;
          this.uploadProgress = `正在上传... ${percent}%`;
        }
      );
      this.uploadProgress = buildUploadProgressMessage(data);
      this.selectedFiles = [];
      await this.loadDocuments();

      setTimeout(() => {
        this.uploadProgress = '';
        this.uploadPercent = 0;
      }, 3000);
    } catch (error) {
      this.uploadProgress = `上传失败：${this.handleServiceError(error)}`;
      this.uploadPercent = 0;
    } finally {
      this.isUploading = false;
    }
  },
  async deleteDocument(filename) {
    if (!confirm(`确定要删除文档 "${filename}" 吗？这会同时删除 Milvus 中的相关向量。`)) return;

    try {
      const data = await removeDocument(this.api, this.token, filename);
      alert(data.message);
      await this.loadDocuments();
    } catch (error) {
      alert(`删除文档失败：${this.handleServiceError(error)}`);
    }
  }
};
