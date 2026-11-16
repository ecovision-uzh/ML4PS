"""Check that a Python environment provides everything the ML4PS course notebooks need.

Run it with the python of the environment to check, from anywhere:

    .venv/bin/python tools/check_env.py                  # uv / pip environment
    .venv/bin/python tools/check_env.py --no-torch       # uv base environment, before PyTorch is added
    conda run -n ML4PSenv python tools/check_env.py      # conda environment

It checks that
  1. the installed versions match the pins of 0-Setup/ML4PSrequirements.txt (plus torch, pinned through torchvision),
  2. every package the notebooks import can be imported,
  3. a few smoke operations run (numpy/pandas/sklearn/matplotlib/geopandas, and torch/torchvision/smp),
and prints the torch build (CPU / CUDA) and whether a GPU can actually run a CUDA kernel.

With --no-torch, the deep learning libraries (torch, torchvision, segmentation-models-pytorch) are left out.
Exit code 0 if everything passes, 1 otherwise. A GPU that is visible but cannot run kernels is only a warning.
"""
import argparse
import importlib
import importlib.metadata as md
import re
import sys
import traceback
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Pinned indirectly (torchvision==0.21.0 requires torch==2.6.0) but imported directly by the notebooks
IMPLIED_PINS = {"torch": "2.6.0"}
# Modules imported by the course notebooks (and tester.py of lab 5)
MODULES = [
    "numpy", "pandas", "sklearn", "matplotlib", "matplotlib.pyplot", "mpl_toolkits.mplot3d", "seaborn",
    "geopandas", "geodatasets", "pyogrio", "PIL", "wget", "ipykernel", "nbconvert",
]
TORCH_PACKAGES = ["torch", "torchvision", "segmentation-models-pytorch"]
TORCH_MODULES = ["torch", "torchvision", "segmentation_models_pytorch"]

failures, warnings = [], []


def fail(msg):
    failures.append(msg)
    print(f"  FAIL  {msg}")


def warn(msg):
    warnings.append(msg)
    print(f"  WARN  {msg}")


def ok(msg):
    print(f"  ok    {msg}")


def read_pins(path):
    pins = {}
    for line in Path(path).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if m := re.fullmatch(r"([A-Za-z0-9_.\-]+)\s*==\s*([^\s;]+)", line):
            pins[m.group(1)] = m.group(2)
    return pins


def check_versions(pins):
    print("Versions (installed vs pinned):")
    for name, pinned in pins.items():
        try:
            installed = md.version(name)
        except md.PackageNotFoundError:
            fail(f"{name}: not installed (pinned {pinned})")
            continue
        public = installed.split("+", 1)[0]  # 2.6.0+cpu -> 2.6.0
        (ok if public == pinned else fail)(f"{name}: {installed} (pinned {pinned})")


def check_imports(modules):
    print("Imports:")
    for mod in modules:
        try:
            importlib.import_module(mod)
            ok(mod)
        except Exception as e:  # noqa: BLE001 - report any import problem
            fail(f"import {mod}: {type(e).__name__}: {e}")


def smoke(name, fn):
    try:
        fn()
        ok(name)
    except Exception as e:  # noqa: BLE001
        fail(f"{name}: {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)


def smoke_tests(with_torch):
    import io
    import json

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    print("Smoke tests:")

    def sklearn_fit():
        from sklearn.datasets import load_diabetes
        from sklearn.ensemble import RandomForestRegressor
        X, y = load_diabetes(return_X_y=True)
        RandomForestRegressor(n_estimators=5, random_state=0).fit(X, y).predict(X[:3])

    def plotting():
        import seaborn as sns
        fig, ax = plt.subplots()
        sns.scatterplot(data=pd.DataFrame({"x": np.arange(5), "y": np.arange(5) ** 2}), x="x", y="y", ax=ax)
        fig.savefig(io.BytesIO(), format="png")
        plt.close(fig)

    def geopandas_io():
        import geopandas as gpd
        geojson = {"type": "FeatureCollection", "features": [{
            "type": "Feature", "properties": {"name": "a"},
            "geometry": {"type": "LineString", "coordinates": [[8.5, 47.3], [8.6, 47.4]]}}]}
        gdf = gpd.read_file(io.BytesIO(json.dumps(geojson).encode()))
        gdf.set_crs(epsg=4326, allow_override=True).to_crs(epsg=3035).length.sum()

    def torch_cpu():
        import segmentation_models_pytorch as smp
        import torch
        from torchvision import models, transforms
        x = torch.rand(2, 3, 64, 64)
        x = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])(x)
        loss = models.resnet18(weights=None)(x).sum()
        loss.backward()
        smp.Unet(encoder_name="resnet18", encoder_weights=None, classes=3)(x)

    smoke("scikit-learn fit/predict", sklearn_fit)
    smoke("matplotlib + seaborn plot", plotting)
    smoke("geopandas read GeoJSON + reproject", geopandas_io)
    if with_torch:
        smoke("torch/torchvision/smp forward+backward (CPU)", torch_cpu)


def torch_report():
    import torch
    print("Torch build:")
    cuda_build = torch.version.cuda
    print(f"  torch {torch.__version__}, CUDA build: {cuda_build}, cuda.is_available(): {torch.cuda.is_available()}")
    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        print("  Apple MPS available")
    if cuda_build is not None:
        if torch.backends.cudnn.version() is None:
            fail("CUDA build of torch, but cuDNN cannot be loaded (nvidia-* packages missing?)")
        else:
            ok(f"CUDA {cuda_build} build with cuDNN {torch.backends.cudnn.version()}")
    # Whether this machine's GPU can use the build is reported, but is not a property of the environment
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        cap = ".".join(map(str, torch.cuda.get_device_capability(0)))
        try:
            x = torch.rand(256, 256, device="cuda")
            (x @ x).sum().item()
            ok(f"CUDA kernel ran on {name} (compute capability {cap})")
        except Exception as e:  # noqa: BLE001
            warn(f"GPU {name} (compute capability {cap}) visible but cannot run CUDA kernels with this build: "
                 f"{type(e).__name__}: {str(e).splitlines()[0]}")
        print(f"  architectures compiled in this build: {' '.join(torch.cuda.get_arch_list())}")
    elif cuda_build is not None:
        warn("CUDA build installed but no usable GPU/driver found")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--requirements", default=REPO / "0-Setup" / "ML4PSrequirements.txt",
                        help="pip requirements file with the pinned versions (default: %(default)s)")
    parser.add_argument("--no-torch", action="store_true",
                        help="leave out the deep learning libraries (uv base environment)")
    args = parser.parse_args()
    with_torch = not args.no_torch

    pins = {**read_pins(args.requirements), **IMPLIED_PINS}
    modules = MODULES + TORCH_MODULES if with_torch else MODULES
    if not with_torch:
        pins = {name: v for name, v in pins.items() if name not in TORCH_PACKAGES}

    print(f"Python {sys.version.split()[0]} at {sys.executable}")
    check_versions(pins)
    check_imports(modules)
    if not any(f.startswith("import ") for f in failures):
        smoke_tests(with_torch)
        if with_torch:
            torch_report()
    print(f"RESULT: {'FAIL' if failures else 'PASS'} ({len(failures)} failure(s), {len(warnings)} warning(s))")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
