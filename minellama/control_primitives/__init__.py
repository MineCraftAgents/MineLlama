from pathlib import Path
import os
import minellama.utils as U


def load_control_primitives(primitive_names=None):
    # package_path = pkg_resources.resource_filename("voyager", "")
    package_path = Path(__file__).parent
    if primitive_names is None:
        primitive_names = [
            primitives[:-3]
            for primitives in os.listdir(f"{package_path}")
            if primitives.endswith(".js")
        ]
    primitives = [
        U.load_text(f"{package_path}/{primitive_name}.js")
        for primitive_name in primitive_names
    ]
    return primitives
