"""
AbirQu Theme Manager
Copyright 2026 Abir Maheshwari

Dark/Light theme support for the quantum IDE.
"""
from typing import Dict, Any


class ThemeColors:
    """Color definitions for a theme."""

    def __init__(self, colors: Dict[str, str]):
        self._colors = colors

    def __getattr__(self, name: str) -> str:
        if name.startswith('_'):
            return super().__getattribute__(name)
        return self._colors.get(name, '#FFFFFF')


DARK_THEME = {
    'name': 'dark',
    'bg_primary': '#1a1a2e',
    'bg_secondary': '#16213e',
    'bg_tertiary': '#0f3460',
    'bg_panel': '#1e1e2e',
    'bg_editor': '#0d1117',
    'bg_input': '#21262d',
    'text_primary': '#e6edf3',
    'text_secondary': '#8b949e',
    'text_muted': '#484f58',
    'accent_primary': '#7c3aed',
    'accent_secondary': '#a855f7',
    'accent_success': '#3fb950',
    'accent_warning': '#d29922',
    'accent_error': '#f85149',
    'border': '#30363d',
    'border_focus': '#7c3aed',
    'shadow': '#00000080',
    'gate_h': '#7c3aed',
    'gate_x': '#f85149',
    'gate_y': '#d29922',
    'gate_z': '#3fb950',
    'gate_cnot': '#58a6ff',
    'gate_cz': '#58a6ff',
    'gate_s': '#a855f7',
    'gate_t': '#f0883e',
    'gate_rx': '#f85149',
    'gate_ry': '#d29922',
    'gate_rz': '#3fb950',
    'gate_swap': '#da3633',
    'gate_toffoli': '#bc8cff',
    'wire': '#8b949e',
    'wire_active': '#58a6ff',
    'measurement': '#f0883e',
    'grid_line': '#21262d',
    'selection': '#7c3aed40',
    'hover': '#ffffff10',
    'scrollbar_bg': '#161b22',
    'scrollbar_thumb': '#30363d',
    'menu_bg': '#1e1e2e',
    'menu_hover': '#21262d',
    'toolbar_bg': '#16161e',
    'tab_active': '#7c3aed',
    'tab_inactive': '#30363d',
    'chart_bar': '#7c3aed',
    'chart_bar_alt': '#a855f7',
    'chart_grid': '#21262d',
    'chart_text': '#8b949e',
}

LIGHT_THEME = {
    'name': 'light',
    'bg_primary': '#ffffff',
    'bg_secondary': '#f6f8fa',
    'bg_tertiary': '#eaeef2',
    'bg_panel': '#ffffff',
    'bg_editor': '#ffffff',
    'bg_input': '#f6f8fa',
    'text_primary': '#1f2328',
    'text_secondary': '#656d76',
    'text_muted': '#8b949e',
    'accent_primary': '#7c3aed',
    'accent_secondary': '#a855f7',
    'accent_success': '#1a7f37',
    'accent_warning': '#9a6700',
    'accent_error': '#cf222e',
    'border': '#d0d7de',
    'border_focus': '#7c3aed',
    'shadow': '#00000010',
    'gate_h': '#7c3aed',
    'gate_x': '#cf222e',
    'gate_y': '#9a6700',
    'gate_z': '#1a7f37',
    'gate_cnot': '#0969da',
    'gate_cz': '#0969da',
    'gate_s': '#8250df',
    'gate_t': '#bc4c00',
    'gate_rx': '#cf222e',
    'gate_ry': '#9a6700',
    'gate_rz': '#1a7f37',
    'gate_swap': '#a40e26',
    'gate_toffoli': '#8250df',
    'wire': '#656d76',
    'wire_active': '#0969da',
    'measurement': '#bc4c00',
    'grid_line': '#eaeef2',
    'selection': '#7c3aed20',
    'hover': '#00000008',
    'scrollbar_bg': '#f6f8fa',
    'scrollbar_thumb': '#d0d7de',
    'menu_bg': '#ffffff',
    'menu_hover': '#f6f8fa',
    'toolbar_bg': '#f6f8fa',
    'tab_active': '#7c3aed',
    'tab_inactive': '#d0d7de',
    'chart_bar': '#7c3aed',
    'chart_bar_alt': '#a855f7',
    'chart_grid': '#eaeef2',
    'chart_text': '#656d76',
}


class ThemeManager:
    """Manages dark/light themes for the quantum IDE."""

    def __init__(self, initial_theme: str = 'dark'):
        self.themes = {
            'dark': ThemeColors(DARK_THEME),
            'light': ThemeColors(LIGHT_THEME),
        }
        self.current_theme_name = initial_theme
        self.current_theme = self.themes[initial_theme]
        self._callbacks = []

    def switch_theme(self, theme_name: str):
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            self.current_theme = self.themes[theme_name]
            for cb in self._callbacks:
                try:
                    cb(theme_name)
                except Exception:
                    pass

    def on_theme_change(self, callback):
        self._callbacks.append(callback)

    def get_color(self, key: str) -> str:
        return getattr(self.current_theme, key, '#FFFFFF')

    def get_css(self) -> str:
        t = self.current_theme._colors
        return f"""
        QMainWindow {{ background-color: {t['bg_primary']}; }}
        QWidget {{ background-color: {t['bg_primary']}; color: {t['text_primary']}; }}
        QMenuBar {{ background-color: {t['toolbar_bg']}; color: {t['text_primary']}; }}
        QMenuBar::item:selected {{ background-color: {t['menu_hover']}; }}
        QMenu {{ background-color: {t['menu_bg']}; color: {t['text_primary']}; }}
        QMenu::item:selected {{ background-color: {t['menu_hover']}; }}
        QToolBar {{ background-color: {t['toolbar_bg']}; border: none; }}
        QTabWidget::pane {{ border: 1px solid {t['border']}; }}
        QTabBar::tab {{ background: {t['tab_inactive']}; color: {t['text_primary']}; padding: 8px 16px; }}
        QTabBar::tab:selected {{ background: {t['tab_active']}; color: white; }}
        QPushButton {{ background-color: {t['accent_primary']}; color: white; border: none;
                       padding: 6px 16px; border-radius: 4px; }}
        QPushButton:hover {{ background-color: {t['accent_secondary']}; }}
        QLineEdit {{ background-color: {t['bg_input']}; color: {t['text_primary']};
                     border: 1px solid {t['border']}; padding: 4px 8px; border-radius: 4px; }}
        QLineEdit:focus {{ border-color: {t['border_focus']}; }}
        QComboBox {{ background-color: {t['bg_input']}; color: {t['text_primary']};
                     border: 1px solid {t['border']}; padding: 4px 8px; }}
        QScrollBar:vertical {{ background: {t['scrollbar_bg']}; width: 8px; }}
        QScrollBar::handle:vertical {{ background: {t['scrollbar_thumb']}; border-radius: 4px; }}
        QSplitter::handle {{ background-color: {t['border']}; }}
        QLabel {{ color: {t['text_primary']}; }}
        QGroupBox {{ border: 1px solid {t['border']}; border-radius: 4px;
                     margin-top: 8px; padding-top: 16px; font-weight: bold; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
        """ + t['bg_primary']

    def list_themes(self):
        return list(self.themes.keys())
