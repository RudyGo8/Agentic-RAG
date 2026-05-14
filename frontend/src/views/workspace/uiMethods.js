import { config } from '../../config';

export const uiMethods = {
  applyTheme() {
    document.body.classList.toggle('theme-dark', this.isDarkMode);
  },
  toggleTheme() {
    this.isDarkMode = !this.isDarkMode;
    localStorage.setItem(config.THEME_STORAGE_KEY, this.isDarkMode ? 'dark' : 'light');
    this.applyTheme();
  },
  handleSettings() {
    if (!this.isAdmin) {
      alert('仅管理员可访问文档管理');
      return;
    }

    this.activeNav = 'settings';
    this.showHistorySidebar = false;
    this.loadDocuments();
  }
};
