from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMenu

from PySide6 import QtCore
from loguru import logger


_web_actions = [QWebEnginePage.Back, QWebEnginePage.Forward,
                QWebEnginePage.Reload,
                QWebEnginePage.Undo, QWebEnginePage.Redo,
                QWebEnginePage.Cut, QWebEnginePage.Copy,
                QWebEnginePage.Paste, QWebEnginePage.SelectAll]

class WebEngineView(QWebEngineView):

    enabled_changed = QtCore.Signal(QWebEnginePage.WebAction, bool)

    @staticmethod
    def web_actions():
        return _web_actions

    @staticmethod
    def minimum_zoom_factor():
        return 0.25

    @staticmethod
    def maximum_zoom_factor():
        return 5

    def __init__(self, tab_factory_func, window_factory_func):
        super().__init__()
        self._tab_factory_func = tab_factory_func
        self._window_factory_func = window_factory_func
        page = self.page()
        self._actions = {}
        for web_action in WebEngineView.web_actions():
            action = page.action(web_action)
            action.changed.connect(self._enabled_changed)
            self._actions[action] = web_action

    def contextMenuEvent(self, event):
          menu = QMenu(self)
        #   quitAction = menu.addAction("Quit")
          OpenNewTabAction = menu.addAction("Open in a new tab")
          OpenNewWindowAction = menu.addAction("Open in a new window")
          action = menu.exec_(self.mapToGlobal(event.pos()))
          if action == OpenNewTabAction:
              # TO Open in a new tab
              logger.debug("Open in New Tab")
          elif action == OpenNewWindowAction:
              # TO Open in a new child window
              logger.debug("Open in New Window")
          else:
              logger.debug("No action")

    def is_web_action_enabled(self, web_action):
        return self.page().action(web_action).isEnabled()

    def createWindow(self, window_type):
        if (window_type == QWebEnginePage.WebBrowserTab or
            window_type == QWebEnginePage.WebBrowserBackgroundTab):
            return self._tab_factory_func()
        return self._window_factory_func()

    def _enabled_changed(self):
        action = self.sender()
        web_action = self._actions[action]
        self.enabled_changed.emit(web_action, action.isEnabled())
