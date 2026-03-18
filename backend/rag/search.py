import json
import logging
from pathlib import Path
import numpy as np
import faiss

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parent.parent.parent
INDEX_PATH = _PROJECT_ROOT / "embeddings" / "cards.index"
ID_MAP_PATH = _PROJECT_ROOT / "embeddings" / "id_map.json"


def build_index(vectors: list[np.ndarray], postgres_ids: list[int]) -> tuple[faiss.Index, dict]:
    """
    Build and save FAISS index from vectors and postgres IDs.
    Returns the index and id_map dict.
    """
    # Create index
    dimension = len(vectors[0]) if vectors else 384
    index = faiss.IndexFlatL2(dimension)

    # Add vectors to index
    if vectors:
        vectors_array = np.array(vectors, dtype='float32')
        index.add(vectors_array)

    # Create id_map: position -> postgres_id
    id_map = {str(i): int(pid) for i, pid in enumerate(postgres_ids)}

    # Save to disk
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))

    with open(ID_MAP_PATH, 'w') as f:
        json.dump(id_map, f)

    logger.info(f"Built FAISS index with {len(vectors)} vectors")
    return index, id_map


def load_index() -> tuple[faiss.Index | None, dict]:
    """
    Load FAISS index and id_map from disk.
    Returns (index, id_map) or (None, {}) if files don't exist.
    """
    if not INDEX_PATH.exists() or not ID_MAP_PATH.exists():
        return None, {}

    try:
        index = faiss.read_index(str(INDEX_PATH))
        with open(ID_MAP_PATH, 'r') as f:
            id_map = json.load(f)
        logger.info(f"Loaded FAISS index with {index.ntotal} vectors")
        return index, id_map
    except Exception as e:
        logger.warning(f"Failed to load FAISS index: {e}")
        return None, {}


def search(index: faiss.Index, id_map: dict, vector: np.ndarray, k: int = 1) -> int | None:
    """
    Search FAISS index for similar vectors.
    Returns postgres_id of the top-k result, or None if no matches.
    """
    if index is None or not id_map:
        return None

    try:
        vector_reshaped = vector.reshape(1, -1).astype('float32')
        distances, indices = index.search(vector_reshaped, k)

        if indices[0][0] == -1:  # No match found
            return None

        position = int(indices[0][0])
        postgres_id = id_map.get(str(position))
        return postgres_id
    except Exception as e:
        logger.warning(f"FAISS search failed: {e}")
        return None
