# src/embed/embedder.py
from pathlib import Path
from typing import List, Union
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

class Embedder:
    def __init__(self, path: Union[str, Path] = None):
        # Par défaut, on cible le dossier embed_models à la racine du projet
        if path is None:
            project_root = Path(__file__).resolve().parents[2]
            path = project_root / "embed_models" / "Xenova" / "paraphrase-multilingual-MiniLM-L12-v2"
        else:
            path = Path(path)
            
        if not path.exists():
            raise FileNotFoundError(
                f"Le dossier du modèle ONNX est introuvable à l'emplacement : {path.resolve()}\n"
                "As-tu bien téléchargé les fichiers (model.onnx, tokenizer.json) ?"
            )

        self.tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.session = ort.InferenceSession(
            str(path / "model.onnx"), providers=["CPUExecutionProvider"]
        )
        self.input_names = {inp.name for inp in self.session.get_inputs()}

    def encode(self, text: str, normalize: bool = True) -> np.ndarray:
        """Génère l'embedding d'un texte unique."""
        return self.encode_batch([text], normalize=normalize)[0]

    def encode_batch(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        """Génère les embeddings pour un lot de textes de manière vectorisée."""
        if not texts:
            return np.empty((0, 384)) # Dimension typique de MiniLM

        self.tokenizer.enable_padding()
        encoded = self.tokenizer.encode_batch(texts)
        
        feed = {}
        if "input_ids" in self.input_names:
            feed["input_ids"] = np.array([e.ids for e in encoded], dtype=np.int64)
        if "attention_mask" in self.input_names:
            feed["attention_mask"] = np.array(
                [e.attention_mask for e in encoded], dtype=np.int64
            )
        if "token_type_ids" in self.input_names:
            feed["token_type_ids"] = np.array(
                [e.type_ids for e in encoded], dtype=np.int64
            )
            
        # Inférence ONNX
        hidden = self.session.run(None, feed)[0]
        
        # Mean Pooling manuel via NumPy
        mask = feed["attention_mask"][..., None]
        pooled = (hidden * mask).sum(axis=1) / mask.sum(axis=1)
        
        # Normalisation L2 optionnelle
        if normalize:
            pooled = pooled / np.linalg.norm(pooled, axis=1, keepdims=True)

        return pooled
