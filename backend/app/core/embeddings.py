import hashlib
import logging

import numpy as np

logger = logging.getLogger(__name__)

_model = None


def generate_mock_embedding(text: str) -> list[float]:
    """
    Generates a deterministic 384-dimensional unit vector based on the SHA-256 hash
    of the input text. This acts as a reliable fallback when sentence-transformers
    is offline or unavailable.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:4], byteorder="big")
    rng = np.random.default_rng(seed)
    vec = rng.normal(size=384)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def get_embedding(text: str) -> list[float]:
    """
    Generates a 384-dimensional text embedding using all-MiniLM-L6-v2,
    falling back to a deterministic projection if Hugging Face or dependencies fail.
    """
    global _model
    try:
        if _model is None:
            # Attempt to import and load sentence transformers
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer("all-MiniLM-L6-v2")
        vec = _model.encode(text)
        if hasattr(vec, "tolist"):
            return vec.tolist()
        return list(vec)
    except Exception as e:
        logger.warning(
            f"Failed to generate sentence embedding with HuggingFace (falling back to mock): {e}"
        )
        return generate_mock_embedding(text)
