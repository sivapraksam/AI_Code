"""
RAGAS Evaluation Module.
Evaluates the RAG pipeline against the golden Q&A set.
Target metrics: Faithfulness ≥ 0.90, Context Recall ≥ 0.85.

Uses RAGAS library for automated evaluation.
"""

import json
from pathlib import Path
from typing import List, Optional
from loguru import logger
from rich.console import Console
from rich.table import Table

from config import settings

console = Console()

# RAGAS target thresholds
FAITHFULNESS_TARGET = 0.90
CONTEXT_RECALL_TARGET = 0.85
CONTEXT_PRECISION_TARGET = 0.80


def load_golden_set(golden_set_path: Optional[Path] = None) -> List[dict]:
    """Load the golden Q&A pairs from the JSON file."""
    path = golden_set_path or settings.golden_set_file
    if not path.exists():
        raise FileNotFoundError(f"Golden set not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        pairs = json.load(f)
    logger.info(f"Loaded {len(pairs)} golden Q&A pairs from {path}")
    return pairs


def collect_rag_outputs(golden_pairs: List[dict]) -> List[dict]:
    """
    Run each golden question through the RAG pipeline and collect outputs.
    Returns list of dicts with: question, answer, contexts, ground_truth.
    """
    from src.pipeline.rag_pipeline import get_rag_pipeline
    pipeline = get_rag_pipeline()
    outputs = []

    for i, pair in enumerate(golden_pairs, 1):
        question = pair["question"]
        ground_truth = pair["ground_truth"]
        logger.info(f"[{i}/{len(golden_pairs)}] Processing: {question[:60]}...")

        try:
            response = pipeline.query(question=question)
            contexts = [chunk["content"] for chunk in response.retrieved_chunks]
            outputs.append({
                "question": question,
                "answer": response.answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
                "confidence": response.confidence,
                "citations": response.citations,
                "latency_ms": response.latency_ms,
            })
        except Exception as exc:
            logger.error(f"Error processing question {pair['id']}: {exc}")
            outputs.append({
                "question": question,
                "answer": "ERROR: Could not generate answer.",
                "contexts": [],
                "ground_truth": ground_truth,
                "confidence": "LOW",
                "citations": [],
                "latency_ms": 0,
            })

    return outputs


def run_ragas_evaluation(
    golden_set_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> dict:
    """
    Full RAGAS evaluation pipeline.
    Returns dict with metric scores and pass/fail status.
    """
    logger.info("Starting RAGAS evaluation...")

    golden_pairs = load_golden_set(golden_set_path)
    rag_outputs = collect_rag_outputs(golden_pairs)

    # LLM-based scoring using Gemini API directly (sequential, rate-limit-safe)
    try:
        scores = _gemini_llm_scores(rag_outputs)
        logger.info(f"Gemini LLM scores — faithfulness={scores['faithfulness']:.4f}, "
                    f"context_recall={scores['context_recall']:.4f}, "
                    f"context_precision={scores['context_precision']:.4f}")
    except Exception as exc:
        logger.warning(f"Gemini LLM evaluation failed: {exc}")
        logger.info("Falling back to heuristic scoring for demonstration...")
        scores = _heuristic_scores(rag_outputs)

    # Determine pass/fail
    scores["faithfulness_pass"] = scores["faithfulness"] >= FAITHFULNESS_TARGET
    scores["context_recall_pass"] = scores["context_recall"] >= CONTEXT_RECALL_TARGET
    scores["context_precision_pass"] = scores["context_precision"] >= CONTEXT_PRECISION_TARGET
    scores["overall_pass"] = scores["faithfulness_pass"] and scores["context_recall_pass"]

    # Print scorecard
    _print_scorecard(scores, rag_outputs)

    # Save results
    if output_path is None:
        output_path = Path("./data/evaluation_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "scores": scores,
            "outputs": rag_outputs,
            "thresholds": {
                "faithfulness": FAITHFULNESS_TARGET,
                "context_recall": CONTEXT_RECALL_TARGET,
                "context_precision": CONTEXT_PRECISION_TARGET,
            },
        }, f, indent=2, ensure_ascii=False)
    logger.info(f"Evaluation results saved to: {output_path}")

    return scores


def _gemini_llm_scores(outputs: List[dict]) -> dict:
    """
    Compute RAGAS-style faithfulness, context_recall, and context_precision
    scores by calling the Gemini API directly, one request at a time.

    Sequential execution with a 5-second inter-call delay keeps throughput
    well below the free-tier limit (15 RPM), so no 429s occur.
    """
    import time
    import re
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)

    _CALL_DELAY = 5  # seconds between API calls (12 RPM, safe under 15 RPM)

    def _call(prompt: str) -> str:
        for attempt in range(5):
            try:
                resp = model.generate_content(prompt)
                return resp.text.strip()
            except Exception as exc:
                if attempt < 4 and ("429" in str(exc) or "quota" in str(exc).lower()):
                    wait = 30 * (attempt + 1)
                    logger.warning(f"Rate limit on attempt {attempt+1}, waiting {wait}s…")
                    time.sleep(wait)
                else:
                    raise
        return ""

    def _extract_score(text: str) -> float:
        """Parse a 0-1 float from the LLM response."""
        m = re.search(r"([01](?:\.\d+)?|\.\d+)", text)
        return max(0.0, min(1.0, float(m.group(1)))) if m else 0.5

    faith_scores, recall_scores, prec_scores = [], [], []
    total = len(outputs)

    for i, o in enumerate(outputs, 1):
        q = o["question"]
        ans = o["answer"]
        ctx = "\n---\n".join(o["contexts"][:5])  # limit context length
        gt = o["ground_truth"]

        logger.info(f"LLM scoring [{i}/{total}]: faithfulness…")
        faith_prompt = (
            "You are an evaluation assistant.\n"
            "Given the CONTEXT passages and the ANSWER, score how faithful the answer "
            "is to the context. A score of 1.0 means every claim in the answer is "
            "directly supported by the context. A score of 0.0 means the answer "
            "contains claims not found in the context.\n\n"
            f"CONTEXT:\n{ctx}\n\n"
            f"ANSWER:\n{ans}\n\n"
            "Respond with only a decimal number between 0 and 1 (e.g. 0.85)."
        )
        faith_scores.append(_extract_score(_call(faith_prompt)))
        time.sleep(_CALL_DELAY)

        logger.info(f"LLM scoring [{i}/{total}]: context_recall…")
        recall_prompt = (
            "You are an evaluation assistant.\n"
            "Given the CONTEXT passages and the GROUND TRUTH answer, score how much "
            "of the ground truth information is present in the context. A score of "
            "1.0 means all ground truth statements are in the context. A score of "
            "0.0 means none are.\n\n"
            f"CONTEXT:\n{ctx}\n\n"
            f"GROUND TRUTH:\n{gt}\n\n"
            "Respond with only a decimal number between 0 and 1 (e.g. 0.90)."
        )
        recall_scores.append(_extract_score(_call(recall_prompt)))
        time.sleep(_CALL_DELAY)

        logger.info(f"LLM scoring [{i}/{total}]: context_precision…")
        prec_prompt = (
            "You are an evaluation assistant.\n"
            "Given the QUESTION and the CONTEXT passages, score how relevant and "
            "precise the context is for answering the question. A score of 1.0 means "
            "the context is perfectly relevant. A score of 0.0 means it is "
            "completely irrelevant.\n\n"
            f"QUESTION:\n{q}\n\n"
            f"CONTEXT:\n{ctx}\n\n"
            "Respond with only a decimal number between 0 and 1 (e.g. 0.80)."
        )
        prec_scores.append(_extract_score(_call(prec_prompt)))
        if i < total:
            time.sleep(_CALL_DELAY)

    n = len(outputs)
    return {
        "faithfulness":        round(sum(faith_scores) / n, 4),
        "context_recall":      round(sum(recall_scores) / n, 4),
        "context_precision":   round(sum(prec_scores) / n, 4),
        "num_questions":       n,
        "note": "Gemini LLM-based scores (RAGAS-style prompts, sequential evaluation)",
    }


def _heuristic_scores(outputs: List[dict]) -> dict:
    """
    Compute simple heuristic scores when RAGAS LLM evaluation is unavailable.
    Checks whether citations appear in answers (proxy for faithfulness).
    """
    total = len(outputs)
    if total == 0:
        return {"faithfulness": 0.0, "context_recall": 0.0, "context_precision": 0.0, "num_questions": 0}

    # Heuristic 1: Faithfulness proxy — answer contains at least one [Source:] citation
    faithful_count = sum(
        1 for o in outputs
        if "[Source:" in o["answer"] or "Source:" in o["answer"]
    )

    # Heuristic 2: Context recall proxy — ground truth keywords appear in contexts
    recall_count = 0
    for o in outputs:
        gt_words = set(o["ground_truth"].lower().split())
        context_text = " ".join(o["contexts"]).lower()
        context_words = set(context_text.split())
        overlap = len(gt_words & context_words) / max(len(gt_words), 1)
        if overlap >= 0.3:
            recall_count += 1

    # Heuristic 3: Context precision proxy — retrieved contexts are non-empty
    precision_count = sum(1 for o in outputs if len(o["contexts"]) >= 3)

    return {
        "faithfulness": round(faithful_count / total, 4),
        "context_recall": round(recall_count / total, 4),
        "context_precision": round(precision_count / total, 4),
        "num_questions": total,
        "note": "Heuristic scores (RAGAS LLM evaluation unavailable — check GEMINI_API_KEY)",
    }


def _print_scorecard(scores: dict, outputs: List[dict]) -> None:
    """Print a formatted RAGAS scorecard to the console."""
    console.print("\n")
    console.rule("[bold blue]RAGAS EVALUATION SCORECARD[/bold blue]")

    table = Table(title="Compliance Knowledge Agent — Metric Results", show_header=True)
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Score", justify="right", width=10)
    table.add_column("Target", justify="right", width=10)
    table.add_column("Status", justify="center", width=10)

    def status_icon(passed: bool) -> str:
        return "[green]PASS ✓[/green]" if passed else "[red]FAIL ✗[/red]"

    table.add_row(
        "Faithfulness",
        f"{scores['faithfulness']:.4f}",
        f"≥ {FAITHFULNESS_TARGET}",
        status_icon(scores["faithfulness_pass"]),
    )
    table.add_row(
        "Context Recall",
        f"{scores['context_recall']:.4f}",
        f"≥ {CONTEXT_RECALL_TARGET}",
        status_icon(scores["context_recall_pass"]),
    )
    table.add_row(
        "Context Precision",
        f"{scores['context_precision']:.4f}",
        f"≥ {CONTEXT_PRECISION_TARGET}",
        status_icon(scores["context_precision_pass"]),
    )

    console.print(table)

    overall_style = "bold green" if scores["overall_pass"] else "bold red"
    overall_text = "PASSED" if scores["overall_pass"] else "FAILED"
    console.print(f"\n[{overall_style}]Overall: {overall_text}[/{overall_style}]")
    console.print(f"Questions evaluated: {scores['num_questions']}")

    if "note" in scores:
        console.print(f"\n[yellow]Note: {scores['note']}[/yellow]")

    # Per-question summary
    console.print("\n[bold]Per-Question Confidence Summary:[/bold]")
    q_table = Table(show_header=True)
    q_table.add_column("ID", width=6)
    q_table.add_column("Question (truncated)", width=50)
    q_table.add_column("Confidence", width=12)
    q_table.add_column("Citations", width=10)

    for i, o in enumerate(outputs, 1):
        q_table.add_row(
            str(i),
            o["question"][:48] + "..." if len(o["question"]) > 48 else o["question"],
            o.get("confidence", "N/A"),
            str(len(o.get("citations", []))),
        )
    console.print(q_table)
    console.rule()
