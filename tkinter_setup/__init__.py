import os
import importlib
import inspect
from typing import TYPE_CHECKING

__all__ = []

# === Dynamiczne importowanie klas ===
package_dir = os.path.dirname(__file__)

for filename in os.listdir(package_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = filename[:-3]
        module = importlib.import_module(f"{__name__}.{module_name}")

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ == module.__name__:
                globals()[name] = obj
                __all__.append(name)

# === Statyczne importy tylko dla edytora (VS Code / Pylance) ===
if TYPE_CHECKING:
    from .draws_states import DrawsStates
    from .clip_tkinter_data import ClipTkinterData
    from .left_frame_widgets import LeftFrameWidgets
    from .file_manager import VideoFiles
