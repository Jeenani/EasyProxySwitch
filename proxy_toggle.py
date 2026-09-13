"""
Proxy Switcher (Fluent, Windows 11 style) - управление системным прокси Windows.
Зависимости:
    pip install PyQt5 PyQt-Fluent-Widgets
"""

import sys

try:
    import winreg
    import ctypes
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout

from qfluentwidgets import (
    FluentWindow,
    LineEdit,
    SwitchButton,
    PrimaryPushButton,
    PushButton,
    TitleLabel,
    BodyLabel,
    CaptionLabel,
    InfoBar,
    InfoBarPosition,
    setTheme,
    Theme,
    setThemeColor,
    FluentIcon as FIF,
)

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
INTERNET_OPTION_SETTINGS_CHANGED = 39
INTERNET_OPTION_REFRESH = 37


def notify_system():
    if not IS_WINDOWS:
        return
    internet_set_option = ctypes.windll.wininet.InternetSetOptionW
    internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
    internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)


def read_proxy_settings():
    result = {"enabled": False, "server": "", "override": ""}
    if not IS_WINDOWS:
        return result
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        for name, default in (("ProxyEnable", 0), ("ProxyServer", ""), ("ProxyOverride", "")):
            try:
                val = winreg.QueryValueEx(key, name)[0]
            except FileNotFoundError:
                val = default
            if name == "ProxyEnable":
                result["enabled"] = bool(val)
            elif name == "ProxyServer":
                result["server"] = val
            else:
                result["override"] = val
        winreg.CloseKey(key)
    except OSError:
        pass
    return result


def write_proxy_settings(enabled: bool, server: str, override: str):
    if not IS_WINDOWS:
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1 if enabled else 0)
        if server:
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, server)
        winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, override)
        winreg.CloseKey(key)
        notify_system()
        return True
    except OSError:
        return False


class ProxyPanel(QWidget):
    """Основная страница с настройками прокси."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("ProxyPanel")
        self._build_ui()
        # Небольшая задержка перед загрузкой значений - обходит баг
        # QFluentWidgets, когда LineEdit не перерисовывается сразу
        # после программного setText() до первого show/paint события.
        QTimer.singleShot(0, self._load_current)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 32, 36, 32)
        root.setSpacing(18)

        title = TitleLabel("Системный прокси")
        root.addWidget(title)

        self.status_label = CaptionLabel("Статус: —")
        root.addWidget(self.status_label)

        switch_row = QHBoxLayout()
        switch_row.addWidget(BodyLabel("Включить прокси"))
        switch_row.addStretch()
        self.switch = SwitchButton()
        self.switch.checkedChanged.connect(self._on_switch_changed)
        switch_row.addWidget(self.switch)
        root.addLayout(switch_row)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignLeft)

        self.ip_edit = LineEdit()
        self.ip_edit.setPlaceholderText("например 172.22.245.15")
        self.ip_edit.setClearButtonEnabled(True)

        self.port_edit = LineEdit()
        self.port_edit.setPlaceholderText("например 8888")
        self.port_edit.setClearButtonEnabled(True)

        self.override_edit = LineEdit()
        self.override_edit.setPlaceholderText("localhost;127.*;10.*")
        self.override_edit.setClearButtonEnabled(True)

        form.addRow(BodyLabel("IP-адрес:"), self.ip_edit)
        form.addRow(BodyLabel("Порт:"), self.port_edit)
        form.addRow(BodyLabel("Исключения:"), self.override_edit)
        root.addLayout(form)

        root.addStretch()

        btn_row = QHBoxLayout()
        self.save_btn = PrimaryPushButton(FIF.SAVE, "Сохранить и применить")
        self.save_btn.clicked.connect(self._on_save)
        self.refresh_btn = PushButton(FIF.SYNC, "Обновить")
        self.refresh_btn.clicked.connect(self._load_current)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.refresh_btn)
        root.addLayout(btn_row)

    def _load_current(self):
        settings = read_proxy_settings()
        server = settings.get("server", "")
        if ":" in server:
            ip, port = server.rsplit(":", 1)
        else:
            ip, port = server, ""

        self.ip_edit.setText(ip)
        self.port_edit.setText(port)
        self.override_edit.setText(settings.get("override", ""))

        # Форсируем перерисовку - лечит баг с "невидимым" текстом в LineEdit
        for w in (self.ip_edit, self.port_edit, self.override_edit):
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()

        enabled = settings.get("enabled", False)
        self.switch.blockSignals(True)
        self.switch.setChecked(enabled)
        self.switch.blockSignals(False)
        self._set_status(enabled)

    def _set_status(self, enabled: bool):
        self.status_label.setText(f"Статус: {'ВКЛЮЧЕН' if enabled else 'выключен'}")

    def _on_switch_changed(self, checked: bool):
        self._apply(checked)

    def _on_save(self):
        self._apply(self.switch.isChecked())

    def _apply(self, enabled: bool):
        ip = self.ip_edit.text().strip()
        port = self.port_edit.text().strip()
        override = self.override_edit.text().strip()

        if enabled and (not ip or not port):
            InfoBar.warning(
                title="Проверка",
                content="Укажите IP-адрес и порт перед включением.",
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self,
            )
            self.switch.blockSignals(True)
            self.switch.setChecked(False)
            self.switch.blockSignals(False)
            return

        server = f"{ip}:{port}" if ip and port else ""
        ok = write_proxy_settings(enabled, server, override)
        if ok:
            self._set_status(enabled)
            InfoBar.success(
                title="Готово",
                content="Прокси включён" if enabled else "Прокси выключен",
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self,
            )
        else:
            InfoBar.error(
                title="Ошибка",
                content="Не удалось изменить настройки реестра.",
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proxy Switcher")
        self.resize(460, 420)

        # Mica-эффект работает только на Windows 11; на более старых
        # системах FluentWindow сам подставит обычный фон.
        try:
            self.setMicaEffectEnabled(True)
        except Exception:
            pass

        self.proxy_panel = ProxyPanel(self)
        self.addSubInterface(self.proxy_panel, FIF.GLOBE, "Прокси")

        # Прячем навигацию слева - она нам не нужна для одной страницы
        self.navigationInterface.setVisible(False)
        self.stackedWidget.setContentsMargins(0, 0, 0, 0)

        # Заголовок окна (текст в титульной полосе) - тот же нативный
        # шрифт, что и в остальном интерфейсе, вместо шрифта по умолчанию.
        self.titleBar.titleLabel.setFont(QFont("Segoe UI Variable Display", 10))


if __name__ == "__main__":
    setTheme(Theme.AUTO)
    setThemeColor("#009faa")

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI Variable Display", 10))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())