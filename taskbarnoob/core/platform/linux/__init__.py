"""Linux Mint (Cinnamon) platform backend."""

from . import desktop, hotkeys, panel
from .backend import LinuxCinnamonBackend

__all__ = ["LinuxCinnamonBackend", "desktop", "hotkeys", "panel"]
