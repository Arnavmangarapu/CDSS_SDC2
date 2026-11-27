"""Download commit-pinned models; no indexing or database writes."""
from huggingface_hub import snapshot_download
from backend.config import settings


def main():
    path = snapshot_download(repo_id=settings.VECTOR_EMBEDDER_MODEL,
        revision=settings.VECTOR_EMBEDDER_REVISION,
        allow_patterns=['*.json', '*.txt', '*.safetensors', '*.bin'])
    print(path)
    if settings.VECTOR_RERANKER_MODEL:
        path = snapshot_download(repo_id=settings.VECTOR_RERANKER_MODEL,
            revision=settings.VECTOR_RERANKER_REVISION,
            allow_patterns=['*.json', '*.txt', 'model.safetensors'])
        print(path)


if __name__ == '__main__':
    main()
