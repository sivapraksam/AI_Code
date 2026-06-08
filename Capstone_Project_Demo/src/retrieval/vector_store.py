"""
ChromaDB vector store for compliance document chunks.
Handles upsert, similarity search, and metadata filtering.
"""

from typing import List, Optional
from loguru import logger

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings
from src.domain.policy.models import DocumentChunk


class VectorStore:
    """ChromaDB-backed vector store for document chunks."""

    def __init__(self):
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None

    def _init(self):
        if self._client is None:
            persist_dir = str(settings.chroma_persist_path)
            settings.chroma_persist_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initialising ChromaDB at: {persist_dir}")
            self._client = chromadb.PersistentClient(
                path=persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(
                f"ChromaDB collection '{settings.chroma_collection_name}' ready. "
                f"Documents: {self._collection.count()}"
            )

    @property
    def collection(self):
        self._init()
        return self._collection

    def upsert_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]) -> None:
        """Add or update document chunks and their embeddings in the vector store."""
        if not chunks or not embeddings:
            return
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch: {len(chunks)} chunks vs {len(embeddings)} embeddings")

        # ChromaDB requires string IDs and flat metadata values
        ids = [c.chunk_id for c in chunks]
        documents = [c.content for c in chunks]
        metadatas = []
        for c in chunks:
            meta = {k: (str(v) if v is not None else "") for k, v in c.metadata.items()}
            meta["citation"] = c.citation
            metadatas.append(meta)

        # Batch upsert
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i: i + batch_size],
                embeddings=embeddings[i: i + batch_size],
                documents=documents[i: i + batch_size],
                metadatas=metadatas[i: i + batch_size],
            )
        logger.info(f"Upserted {len(chunks)} chunk(s) into ChromaDB.")

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        document_type_filter: Optional[str] = None,
    ) -> List[dict]:
        """
        Retrieve top_k most similar chunks for a query embedding.
        Returns list of dicts with keys: id, content, metadata, distance.
        """
        where = {"document_type": document_type_filter} if document_type_filter else None
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except TypeError as exc:
            # Some older/incompatible local Chroma metadata states can surface
            # as: "object of type 'int' has no len()" during sequence decoding.
            if "has no len" in str(exc):
                raise RuntimeError(
                    "Chroma local index is incompatible/corrupted. "
                    "Reset data/chroma_db and re-run ingestion."
                ) from exc
            raise

        hits = []
        if results and results["ids"]:
            for idx, chunk_id in enumerate(results["ids"][0]):
                hits.append({
                    "id": chunk_id,
                    "content": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "distance": results["distances"][0][idx],
                    "score": 1.0 - results["distances"][0][idx],  # cosine similarity
                })
        return hits

    def count(self) -> int:
        """Return total number of stored chunks."""
        return self.collection.count()

    def delete_collection(self) -> None:
        """Drop and recreate the collection (use for re-ingestion)."""
        self._init()
        self._client.delete_collection(settings.chroma_collection_name)
        self._collection = self._client.create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.warning(f"Collection '{settings.chroma_collection_name}' deleted and recreated.")


# Module-level singleton
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
