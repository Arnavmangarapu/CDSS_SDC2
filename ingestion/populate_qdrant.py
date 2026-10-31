"""Index complete selected textbooks into a new, non-destructive collection."""
import argparse
import hashlib
import json
import uuid
from pathlib import Path

from backend.config import settings

ENCODER = settings.VECTOR_EMBEDDER_MODEL
TEXTBOOKS = Path(__file__).resolve().parents[1] / 'datasets/literature/MedQA/MedQA-USMLE/textbooks/en'


def chunk_text(text, chunk_size=150, overlap=20):
    if chunk_size <= overlap or overlap < 0:
        raise ValueError('Require 0 <= overlap < chunk_size')
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size-overlap)]


def textbook_chunks(paths):
    for path in paths:
        path = Path(path).resolve()
        if path.parent != TEXTBOOKS.resolve() or path.suffix != '.txt':
            raise ValueError('Only files from the textbook directory are admitted; never index exam questions/keys')
        data = path.read_bytes()
        checksum = hashlib.sha256(data).hexdigest()
        for index, text in enumerate(chunk_text(data.decode('utf-8'))):
            yield {'id': str(uuid.uuid5(uuid.NAMESPACE_URL, f'{path.name}:{checksum}:{index}')),
                   'payload': {'text': text, 'source': path.stem, 'document_sha256': checksum,
                               'chunk_index': index, 'corpus_kind': 'textbook'}}


def main():
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from sentence_transformers import SentenceTransformer
    import torch
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', default=settings.VECTOR_COLLECTION_TEXTBOOKS)
    parser.add_argument('--files', nargs='+', default=['First_Aid_Step1.txt', 'Pathoma_Husain.txt'])
    parser.add_argument('--all-textbooks', action='store_true')
    parser.add_argument('--manifest', type=Path, required=True)
    args=parser.parse_args()
    if args.manifest.exists():parser.error('Use a fresh manifest path')
    paths=sorted(TEXTBOOKS.glob('*.txt')) if args.all_textbooks else [TEXTBOOKS/name for name in args.files]
    chunks=list(textbook_chunks(paths))
    client=QdrantClient(settings.QDRANT_URL, timeout=60)
    if client.collection_exists(args.collection):parser.error('Collection exists; use a new name. Existing collections are never deleted.')
    torch.set_num_threads(4)
    model=SentenceTransformer(ENCODER, revision=settings.VECTOR_EMBEDDER_REVISION,
                              device='cpu', local_files_only=True)
    client.create_collection(args.collection, vectors_config=VectorParams(size=768,distance=Distance.COSINE))
    for offset in range(0,len(chunks),32):
        batch=chunks[offset:offset+32]
        embeddings=model.encode([item['payload']['text'] for item in batch],show_progress_bar=False)
        client.upsert(args.collection, points=[PointStruct(id=item['id'],vector=vector.tolist(),payload=item['payload'])
                                              for item,vector in zip(batch,embeddings)],wait=True)
        print(json.dumps({'indexed':min(offset+32,len(chunks)),'total':len(chunks)}),flush=True)
    actual=client.count(args.collection,exact=True).count
    if actual!=len(chunks):raise RuntimeError('Indexed count does not match source chunks')
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps({'collection':args.collection,'encoder':ENCODER,
        'encoder_revision':settings.VECTOR_EMBEDDER_REVISION,'points':actual,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'character_cap':None,'chunk_size_words':150,'overlap_words':20,'exam_questions_indexed':False},indent=2)+'\n')


if __name__ == '__main__':main()
