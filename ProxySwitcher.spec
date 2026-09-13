# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Модули, которые точно не нужны нашему приложению.
EXCLUDED_MODULES = [
    'numpy',
    'scipy',
    'PIL',
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'PyQt5.QtNetwork',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebEngineCore',
    'PyQt5.QtWebChannel',
    'PyQt5.QtMultimedia',
    'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtBluetooth',
    'PyQt5.QtPositioning',
    'PyQt5.QtNfc',
    'PyQt5.QtSensors',
    'PyQt5.QtSerialPort',
    'PyQt5.QtDBus',
    'PyQt5.QtXmlPatterns',
    'PyQt5.QtPrintSupport',
    'PyQt5.QtTest',
    'PyQt5.QtHelp',
    'PyQt5.QtDesigner',
    'PyQt5.QtOpenGL',
    'tkinter',
    'unittest',
    'pydoc_data',
]

# Бинарники (DLL/PYD), которые PyInstaller всё равно затягивает через хуки
# Qt (обычно как "запасные" рендер-бэкенды или неиспользуемые кодеки).
# Фильтруем их из a.binaries вручную - это надёжнее exclude-module,
# т.к. PyInstaller не считает DLL "модулями".
EXCLUDED_BINARY_SUBSTRINGS = [
    'opengl32sw',       # software OpenGL fallback - не нужен, есть аппаратный
    'd3dcompiler_47',   # компилятор шейдеров для ANGLE/Direct3D бэкенда Qt
    'libgles',          # ANGLE GLES-бэкенд (используем desktop OpenGL)
    'libegl',           # ANGLE EGL-бэкенд
    'mfc140u',          # MFC рантайм - не используется чистым PyQt-приложением
    'qtqml',
    'qtquick',
    'qt5network',
    'qt5webengine',
    'qt5multimedia',
    'qt5bluetooth',
    'qt5positioning',
    'qt5nfc',
    'qt5sensors',
    'qt5serialport',
    'qt5dbus',
    'qt5printsupport',
    'qt5test',
    'qt5designer',
    'qt5opengl',
]


def is_excluded_binary(binary_name: str) -> bool:
    lowered = binary_name.lower()
    return any(token in lowered for token in EXCLUDED_BINARY_SUBSTRINGS)


a = Analysis(
    ['proxy_toggle.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDED_MODULES,
    noarchive=False,
    optimize=2,
)

# Фильтруем бинарники и данные пакета от лишних Qt-DLL и qfluentwidgets-ресурсов
# для неиспользуемых модулей.
a.binaries = TOC([entry for entry in a.binaries if not is_excluded_binary(entry[0])])
a.datas = TOC([entry for entry in a.datas if not is_excluded_binary(entry[0])])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ProxySwitcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
