"""Download the explicit reranker into the ignored local model cache."""
from pathlib import Path
from huggingface_hub import snapshot_download
from backend.config import settings


def main():
    path = snapshot_download(repo_id=settings.VECTOR_RERANKER_MODEL,
        revision=settings.VECTOR_RERANKER_REVISION,
        cache_dir=Path(__file__).resolve().parents[1] / 'datasets/models',
        allow_patterns=['*.json', '*.txt', 'model.safetensors'])
    print(path)


if __name__ == '__main__':
    main()
