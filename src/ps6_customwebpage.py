from PySide6.QtWebEngineCore import QWebEnginePage
from loguru import logger

from PySide6.QtGui import QAction

class CustomWebPage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        
    def createStandardContextMenu(self):
        menu = super().createStandardContextMenu()
        
        # Remove unwanted actions
        actions_to_remove = []
        for action in menu.actions():
            # Check the role of each action
            if action.data() in [QWebEnginePage.NavigationTypeBackForward,
                               QWebEnginePage.NavigationTypeReload,
                               QWebEnginePage.OpenLinkInNewWindow,
                               QWebEnginePage.OpenLinkInNewTab,
                               QWebEnginePage.DownloadLinkToDisk,
                               QWebEnginePage.OpenImageInNewWindow,
                               QWebEnginePage.OpenImageInNewTab,
                               QWebEnginePage.DownloadImageToDisk,
                               QWebEnginePage.OpenMediaInNewWindow,
                               QWebEnginePage.OpenMediaInNewTab,
                               QWebEnginePage.DownloadMediaToDisk]:
                actions_to_remove.append(action)
        
        # Remove the identified actions
        for action in actions_to_remove:
            menu.removeAction(action)

        # Add View Source action if not already present
        view_source_exists = False
        for action in menu.actions():
            if action.text() == "View Page Source":
                view_source_exists = True
                break
                
        if not view_source_exists:
            view_source_action = QAction("View Page Source", menu)
            view_source_action.setShortcut("Ctrl+U")
            view_source_action.triggered.connect(self._view_source)
            menu.addAction(view_source_action)

        return menu
    
    def _view_source(self):
        """Handler for View Source action"""
        self.toHtml(self._show_source_window)
    
    def _show_source_window(self, html):
        """Creates a dialog window to display the page source"""
        from PySide6.QtWidgets import QDialog, QTextEdit, QVBoxLayout
        
        dialog = QDialog(self.view())
        dialog.setWindowTitle("Page Source")
        dialog.resize(800, 600)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(html)
        text_edit.setReadOnly(True)
        
        layout = QVBoxLayout()
        layout.addWidget(text_edit)
        dialog.setLayout(layout)
        dialog.show()
