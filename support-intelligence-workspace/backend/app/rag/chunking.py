"""
Text chunking for RAG.

Keeps chunk boundaries section-aware where possible (headings, paragraphs)
while guaranteeing metadata (chunk_index, total_chunks) on every chunk.
"""

from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.documents import DocumentChunk, LoadedDocument


class DocumentChunker:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 150) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
            length_function=len,
        )

    def chunk(self, document: LoadedDocument) -> list[DocumentChunk]:
        pieces = self._splitter.split_text(document.content)
        if not pieces:
            pieces = [document.content]

        total = len(pieces)
        chunks: list[DocumentChunk] = []
        for index, text in enumerate(pieces):
            meta = document.metadata.model_copy(
                update={"chunk_index": index, "total_chunks": total}
            )
            chunks.append(DocumentChunk(content=text, metadata=meta))
        return chunks

    def chunk_many(self, documents: list[LoadedDocument]) -> list[DocumentChunk]:
        result: list[DocumentChunk] = []
        for doc in documents:
            result.extend(self.chunk(doc))
        return result
