from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_path(value: str) -> Path:
    """Resolve repository-relative settings without depending on the launch directory."""
    return PROJECT_ROOT / Path(value).expanduser()


class Settings(BaseSettings):
    DATASETS_DIR: str = "datasets"
    HPO_PATH: str = "datasets/ontologies/hpo/hp.obo"
    MONDO_PATH: str = "datasets/ontologies/mondo/mondo.obo"
    KG_PATH: str = "datasets/kg.csv"
    DRUGCENTRAL_DIR: str = "datasets/drugcentral"
    MEDQA_DIR: str = "datasets/literature/MedQA"
    MEDMCQA_DIR: str = "datasets/literature/MedMCQA"
    PUBMEDQA_DIR: str = "datasets/literature/pubmedqa-master/pubmedqa-master"
    MEDBULLETS_DIR: str = "datasets/literature/medbulltes5op"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    QDRANT_URL: str = "http://localhost:6333"
    VECTOR_COLLECTION_TEXTBOOKS: str = "medical_textbooks_v2"
    VECTOR_EMBEDDER_MODEL: str = "pritamdeka/S-PubMedBert-MS-MARCO"
    VECTOR_EMBEDDER_REVISION: str = "96786c7024f95c5aac7f2b9a18086c7b97b23036"
    VECTOR_RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    VECTOR_RERANKER_REVISION: str = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
    VECTOR_COLLECTION_PUBMEDQA: str = "pubmedqa_contexts"
    VECTOR_COLLECTION_MEDQA: str = "medqa_train"
    VECTOR_COLLECTION_GUIDELINES: str = "clinical_guidelines"
    VECTOR_COLLECTION_DRUG_LABELS: str = "clinical_drug_labels"

    OPENROUTER_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    COHERE_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    SERPER_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )

settings = Settings()
