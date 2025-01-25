"""Vector store for embeddings."""
from typing import List, Tuple, Optional
from uuid import uuid4, UUID
from datetime import datetime
import numpy as np
from openai import OpenAI
import logfire
import os
import json

from hsi_pdf_agent.models.vector import VectorEntry


class VectorStore:
    """Service for managing vector embeddings."""

    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
        self.entries: List[VectorEntry] = []
        self._load_entries()

    def _load_entries(self) -> None:
        """Load entries from storage."""
        storage_path = os.getenv("VECTOR_STORE_PATH", "data/vector_store.json")
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

        try:
            if os.path.exists(storage_path):
                with open(storage_path, 'r') as f:
                    data = json.load(f)
                    # Convert string IDs back to UUID
                    entries = []
                    for entry_data in data:
                        try:
                            # Convert string ID to UUID
                            entry_data["id"] = UUID(entry_data["id"])
                            # Convert embedding list to numpy array
                            entry_data["embedding"] = [float(x) for x in entry_data["embedding"]]
                            # Convert updated_at string to datetime
                            entry_data["updated_at"] = datetime.fromisoformat(entry_data["updated_at"])
                            # Create VectorEntry
                            entry = VectorEntry.model_validate(entry_data)
                            entries.append(entry)
                        except Exception as e:
                            logfire.error(
                                "vector_entry_load_failed",
                                error=str(e),
                                error_type=type(e).__name__,
                                entry_data=entry_data
                            )
                            continue

                    self.entries = entries
                    logfire.info(
                        "vector_store_loaded",
                        num_entries=len(self.entries),
                        storage_path=storage_path
                    )
        except Exception as e:
            logfire.error(
                "vector_store_load_failed",
                error=str(e),
                error_type=type(e).__name__,
                storage_path=storage_path
            )

    def _save_entries(self) -> None:
        """Save entries to storage."""
        storage_path = os.getenv("VECTOR_STORE_PATH", "data/vector_store.json")
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)

            # Convert entries to JSON-serializable format
            entries_data = []
            for entry in self.entries:
                entry_dict = entry.model_dump()
                # Convert UUID to string for JSON serialization
                entry_dict["id"] = str(entry_dict["id"])
                # Convert datetime to ISO format string
                entry_dict["updated_at"] = entry_dict["updated_at"].isoformat()
                entries_data.append(entry_dict)

            with open(storage_path, 'w') as f:
                json.dump(entries_data, f)

            logfire.info(
                "vector_store_saved",
                num_entries=len(self.entries),
                storage_path=storage_path
            )
        except Exception as e:
            logfire.error(
                "vector_store_save_failed",
                error=str(e),
                error_type=type(e).__name__,
                storage_path=storage_path
            )

    async def add_entry(self, content: str, filename: str = "unknown", page_number: int = 1) -> VectorEntry:
        """Add a new entry to the vector store."""
        embedding = await self._get_embedding(content)
        embedding_list = [float(x) for x in embedding.tolist()]

        entry = VectorEntry(
            id=uuid4(),
            content=content,
            embedding=embedding_list,
            model_name="text-embedding-3-small",
            updated_at=datetime.utcnow(),
            similarity_score=None,
            filename=filename,
            page_number=page_number
        )

        self.entries.append(entry)
        self._save_entries()

        logfire.info(
            "vector_entry_added",
            entry_id=str(entry.id),
            model="text-embedding-3-small"
        )
        return entry

    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding vector for text."""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        embedding_data = response.data[0].embedding
        return np.array([float(x) for x in embedding_data], dtype=np.float64)

    async def search(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Tuple[float, VectorEntry]]:
        """Search for similar entries."""
        if not self.entries:
            return []

        query_embedding = await self._get_embedding(query)

        # Convert stored embeddings to numpy array
        stored_embeddings = np.array([
            entry.embedding for entry in self.entries
        ])

        # Calculate cosine similarities
        similarities = np.dot(stored_embeddings, query_embedding) / (
            np.linalg.norm(stored_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Get indices of top k similar entries
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Create result tuples with similarity scores
        results = []
        for i in top_indices:
            entry = self.entries[i]
            entry.similarity_score = float(similarities[i])
            results.append((float(similarities[i]), entry))

        logfire.info(
            "vector_search_complete",
            query=query,
            num_results=len(results),
            top_k=top_k
        )
        return results
