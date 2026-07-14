# src/embed/download_model.py
import os
import shutil
import logging
from pathlib import Path
from huggingface_hub import hf_hub_download, list_repo_files

os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

ONNX_CANDIDATES = [
    "onnx/model.onnx",
    "onnx/encoder_model.onnx",
    "model.onnx",
]

def download(repo, dest=None):
    # Si aucun chemin n'est fourni, on cible "models/" à la racine du projet
    if dest is None:
        project_root = Path(__file__).resolve().parents[2]
        dest = project_root / "models" / repo
    else:
        dest = Path(dest) / repo
        
    dest.mkdir(parents=True, exist_ok=True)

    print(f"Téléchargement de {repo} vers {dest.resolve()}...")
    files = list_repo_files(repo_id=repo)
    onnx_file = next((c for c in ONNX_CANDIDATES if c in files), None)
    if not onnx_file:
        raise FileNotFoundError(f"No ONNX model found in {repo}")

    for remote, local in [
        ("tokenizer.json", "tokenizer.json"),
        (onnx_file, "model.onnx"),
    ]:
        src = hf_hub_download(repo_id=repo, filename=remote)
        dst = dest / local
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"  saved {dst.name}")
        else:
            print(f"  exists {dst.name}")

    onnx_ext = onnx_file + "_data"
    if onnx_ext in files:
        src = hf_hub_download(repo_id=repo, filename=onnx_ext)
        dst = dest / "model.onnx_data"
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"  saved {dst.name}")
        else:
            print(f"  exists {dst.name}")

if __name__ == "__main__":
    download("Xenova/paraphrase-multilingual-MiniLM-L12-v2")