"""Direct AST and XML injector for Roblox place and model files."""

from roblox_injector.injector import RobloxInjector, inject_bundle
from roblox_injector.parser import PlaceTree

__version__ = "0.2.4"
__all__ = ["RobloxInjector", "inject_bundle", "PlaceTree", "__version__"]
