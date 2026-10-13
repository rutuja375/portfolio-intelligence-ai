class FinBertSentiment:
    """Lazy FinBERT wrapper; model artifacts are never downloaded at import time."""

    MODEL = "ProsusAI/finbert"

    def __init__(self, pipeline=None) -> None:
        self._pipeline = pipeline

    def _load(self):
        if self._pipeline is None:
            from transformers import pipeline

            self._pipeline = pipeline(
                "text-classification", model=self.MODEL, tokenizer=self.MODEL
            )
        return self._pipeline

    def score(self, text: str) -> float:
        if not text.strip():
            return 0.0
        result = self._load()(text[:4000], truncation=True)[0]
        sign = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}
        return sign[result["label"].lower()] * float(result["score"])
