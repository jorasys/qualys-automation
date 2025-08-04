"""
UI package
"""
from .menu_manager import MenuManager, create_scan_menu, create_template_menu, create_vulnerability_menu

__all__ = [
    'MenuManager',
    'create_scan_menu',
    'create_template_menu',
    'create_vulnerability_menu'
]
