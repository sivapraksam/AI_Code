"""
Script: Ingest Documents
Loads all documents from the synthetic_docs directory,
chunks them, embeds with local HF model, and stores in ChromaDB.

Usage:
    python scripts/ingest_documents.py [--reset] [--docs-dir PATH]
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Ingest compliance documents into ChromaDB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing ChromaDB collection before ingesting",
    )
    parser.add_argument(
        "--docs-dir",
        type=str,
        default=None,
        help="Override the documents directory path",
    )
    args = parser.parse_args()

    console.rule("[bold blue]Compliance Knowledge Agent — Document Ingestion[/bold blue]")

    from config import settings

    docs_dir = Path(args.docs_dir) if args.docs_dir else settings.docs_path
    console.print(f"Documents directory: [cyan]{docs_dir}[/cyan]")
    console.print(f"ChromaDB path: [cyan]{settings.chroma_persist_dir}[/cyan]")
    console.print(f"Embedding model: [cyan]{settings.embedding_model}[/cyan]")
    console.print(f"Chunk size: [cyan]{settings.chunk_size}[/cyan] chars, overlap: [cyan]{settings.chunk_overlap}[/cyan]")
    console.print()

    if not docs_dir.exists():
        console.print(f"[red]ERROR: Documents directory does not exist: {docs_dir}[/red]")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Load
        task = progress.add_task("Loading documents...", total=None)
        from src.ingestion.document_loader import load_documents_from_directory
        documents = load_documents_from_directory(docs_dir)
        progress.update(task, description=f"[green]Loaded {len(documents)} documents[/green]")

        if not documents:
            console.print("[red]No documents loaded. Exiting.[/red]")
            sys.exit(1)

        # Step 2: Chunk
        progress.update(task, description="Chunking documents...")
        from src.ingestion.chunker import chunk_document
        all_chunks = []
        for doc in documents:
            chunks = chunk_document(doc, chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
            all_chunks.extend(chunks)
        progress.update(task, description=f"[green]Created {len(all_chunks)} chunks[/green]")

        # Step 3: Embed
        progress.update(task, description="Embedding chunks with local HF model (may take a minute)...")
        from src.ingestion.embedder import get_embedding_model
        embedder = get_embedding_model()
        texts = [c.content for c in all_chunks]
        embeddings = embedder.embed(texts, batch_size=32)
        progress.update(task, description=f"[green]Generated {len(embeddings)} embeddings (dim={embedder.dimension})[/green]")

        # Step 4: Store
        progress.update(task, description="Storing in ChromaDB...")
        from src.retrieval.vector_store import get_vector_store
        vs = get_vector_store()
        if args.reset:
            console.print("[yellow]Resetting vector store...[/yellow]")
            vs.delete_collection()
        vs.upsert_chunks(all_chunks, embeddings)
        total = vs.count()
        progress.update(task, description=f"[green]ChromaDB total: {total} chunks[/green]")

    console.print()
    console.rule()
    console.print(f"[bold green]Ingestion Complete![/bold green]")
    console.print(f"  Documents:  {len(documents)}")
    console.print(f"  Chunks:     {len(all_chunks)}")
    console.print(f"  Embeddings: {len(embeddings)} (dim={embedder.dimension})")
    console.print(f"  DB total:   {total}")
    console.rule()


if __name__ == "__main__":
    main()
