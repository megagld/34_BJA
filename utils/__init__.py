import os
import importlib
import inspect
from typing import TYPE_CHECKING

__all__ = []

package_dir = os.path.dirname(__file__)

# === Dynamiczne importowanie funkcji i klas z utils/*.py ===
for filename in os.listdir(package_dir):
    if filename.endswith(".py") and not filename.startswith("_") and filename != "__init__.py":
        module_name = filename[:-3]
        module = importlib.import_module(f"{__name__}.{module_name}")

        for name, obj in inspect.getmembers(module, lambda x: inspect.isfunction(x) or inspect.isclass(x)):
            if obj.__module__ == module.__name__:
                globals()[name] = obj
                __all__.append(name)

# === Statyczne importy tylko dla Pylance / VS Code ===
if TYPE_CHECKING:
    from .general import letterbox_calc
    from .general import angle_between_vectors
    from .general import rotate_point
    from .general import transform_point
    from .general import get_dist
    from .general import draw_line
