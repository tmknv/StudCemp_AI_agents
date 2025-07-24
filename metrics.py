import os
import re
import json
import itertools
from dataclasses import dataclass
from typing import List, Dict, Any, Callable, Optional

class BaseEvaluator:
    pass

class ReviewEvaluator(BaseEvaluator):
    """
    Оценивает текст рецензии по четырём метрикам:
    1. Полнота (Completeness / CS)
    2. Практическая полезность (Usefulness)
    3. Правдоподобие фактов (Plausibility / TS)
    4. Логическая согласованность (Logical Consistency / LC)
    """

    REQUIRED_BLOCKS = [
        "summary",
        "strengths",
        "weaknesses",
        "suggestions",
        "overall_evaluation",
    ]

    def __init__(self, llm_client, fact_verifier, baseline_tokens: int = 30, **kwargs):
        super().__init__()
        self.llm = llm_client
        self.verifier = fact_verifier
        self.baseline = baseline_tokens

    def evaluate(self, review_text: str, original_paper: Any = None) -> Dict[str, Any]:
        return {
            "completeness": self._eval_completeness(review_text),
            "usefulness": self._eval_usefulness(review_text),
            "plausibility": self._eval_plausibility(review_text, original_paper),
            "consistency": self._eval_logical_consistency(review_text),
        }

    def _eval_completeness(self, text: str) -> float:
        lower = text.lower()
        total_coverage = 0.0
        for block in self.REQUIRED_BLOCKS:
            if re.search(rf"^\s*{block}[:#\-]", lower, re.MULTILINE) or block in lower:
                pattern = rf"{block}[:#\-]?.*?(?=^(?:{'|'.join(self.REQUIRED_BLOCKS)})[:#\-]|\Z)"
                match = re.search(pattern, lower, re.MULTILINE | re.DOTALL)
                tokens = len(match.group(0).split()) if match else 0
                coverage = min(tokens / self.baseline, 1.0)
                total_coverage += coverage
        score = 10 * total_coverage / len(self.REQUIRED_BLOCKS)
        return round(score, 2)

    def _eval_usefulness(self, text: str) -> float:
        parts = re.split(r"\n\s*#+\s*|\n\n+", text)
        scores = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            prompt = (
                "Оцени практическую полезность следующего фрагмента рецензии по шкале от 0 до 10.\n"
                "Верни JSON вида {\"score\": <число>, \"обоснование\": <строка>}.\n\n"
                f"Фрагмент:\n\"\"\"{part}\"\"\""
            )
            res = self.llm.judge(prompt)
            scores.append(res.get("score", 0))
        return round(sum(scores) / max(len(scores), 1), 2)

    def _extract_statements(self, text: str) -> List[str]:
        pattern = (
            r"([^.]*?\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}\b[^.]*?\.)|"
            r"([^.]*?doi:[^\s,]+[^.]*?\.)|"
            r"([^.]*?https?://[^\s]+[^.]*?\.)|"
            r"([^.]*?\b\d+[.,]?\d*\b[^.]*?\.)"
        )
        candidates = re.findall(pattern, text, flags=re.IGNORECASE)
        return [s for tup in candidates for s in tup if s.strip()]

    def _eval_plausibility(self, text: str, original_paper: Any) -> float:
        statements = self._extract_statements(text)
        total = len(statements)
        if total == 0:
            return 5.0
        passed = sum(1 for stmt in statements if self.verifier.verify(stmt, original_paper))
        epsilon = 0.5
        score = 10 * (passed + epsilon) / (total + 2 * epsilon)
        return round(score, 2)

    def _eval_logical_consistency(self, text: str) -> float:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if len(sentences) < 2:
            return 10.0
        pair_scores = []
        for a, b in itertools.combinations(sentences, 2):
            prompt = (
                "Определи, противоречат ли ниже два предложения или согласуются логически.\n"
                "Верни JSON вида {\"label\": \"consistent|contradictory\", \"score\": 0-10, \"обоснование\": <строка>}.\n"
                "Где 10 – полностью согласованы, 0 – явное противоречие.\n\n"
                f"Предложение 1: {a}\n"
                f"Предложение 2: {b}"
            )
            res = self.llm.judge(prompt)
            pair_scores.append(res.get("score", 10))
        return round(sum(pair_scores) / len(pair_scores), 2)