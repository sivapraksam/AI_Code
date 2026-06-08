"""
Script: Run RAGAS Evaluation
Evaluates the RAG pipeline against the 10-question golden Q&A set.
Produces a scorecard with faithfulness, context recall, and context precision.

Target: Faithfulness ≥ 0.90, Context Recall ≥ 0.85

Usage:
    python scripts/run_evaluation.py [--golden-set PATH] [--output PATH]
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from rich.console import Console

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation on the golden Q&A set")
    parser.add_argument(
        "--golden-set",
        type=str,
        default=None,
        help="Path to golden Q&A pairs JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./data/evaluation_results.json",
        help="Output path for evaluation results JSON",
    )
    args = parser.parse_args()

    console.rule("[bold blue]Compliance Knowledge Agent — RAGAS Evaluation[/bold blue]")
    console.print()

    # Validate prerequisites
    from config import settings
    from src.retrieval.vector_store import get_vector_store

    vs = get_vector_store()
    chunk_count = vs.count()
    if chunk_count == 0:
        console.print(
            "[red]ERROR: Vector store is empty. Run `python scripts/ingest_documents.py` first.[/red]"
        )
        sys.exit(1)
    console.print(f"Vector store: [green]{chunk_count} chunks ready[/green]")

    golden_path = Path(args.golden_set) if args.golden_set else settings.golden_set_file
    if not golden_path.exists():
        console.print(f"[red]ERROR: Golden set not found at: {golden_path}[/red]")
        sys.exit(1)
    console.print(f"Golden set: [cyan]{golden_path}[/cyan]")
    console.print()

    if not settings.gemini_api_key:
        console.print(
            "[yellow]WARNING: GEMINI_API_KEY not set. "
            "Evaluation will use heuristic scoring instead of Gemini-based RAGAS.[/yellow]"
        )
        console.print(
            "[yellow]For full RAGAS evaluation, set GEMINI_API_KEY in your .env file.[/yellow]\n"
        )

    console.print("[bold]Starting evaluation...[/bold] (this may take several minutes)\n")

    from src.evaluation.ragas_eval import run_ragas_evaluation
    scores = run_ragas_evaluation(
        golden_set_path=golden_path,
        output_path=Path(args.output),
    )

    console.print(f"\nResults saved to: [cyan]{args.output}[/cyan]")

    # Exit with non-zero code if evaluation fails targets
    if not scores.get("overall_pass", False):
        console.print(
            "\n[bold red]Evaluation targets NOT met. "
            "Review pipeline configuration and document quality.[/bold red]"
        )
        sys.exit(1)
    else:
        console.print("\n[bold green]Evaluation targets MET. Pipeline ready for review.[/bold green]")


if __name__ == "__main__":
    main()
