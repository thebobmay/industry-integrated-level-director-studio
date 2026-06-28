"""Project 3 feedback adapter.

Wraps the Project 3 reception classifier (a TF-IDF vectorizer feeding a linear
SVM) behind the FeedbackAdapter interface. It loads the trained artifacts from
``models/project3_feedback/`` and returns a normalized FeedbackResult.

This is a broad reception signal, positive or negative, not a complete playtest
analysis. The underlying LinearSVC exposes no calibrated probability, so no
confidence score is produced; see Decision 12 in the decision log. The classifier
was trained on game review text, so it generalizes only loosely to playtest notes.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

from ai_level_director.domain.models import FeedbackResult

# Repo root is three levels up from this file: adapters -> ai_level_director -> src.
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL_DIR = _REPO_ROOT / "models" / "project3_feedback"

MODEL_NAME = "project3-tfidf-linear-svm"


class Project3FeedbackAdapter:
    """Classify playtester feedback into a positive or negative reception signal."""

    def __init__(self, model_dir: Path | str = DEFAULT_MODEL_DIR) -> None:
        """Load the vectorizer, classifier, and label mapping from disk."""
        directory = Path(model_dir)
        with (directory / "tfidf_vectorizer.pkl").open("rb") as handle:
            self._vectorizer = pickle.load(handle)
        with (directory / "review_classifier.pkl").open("rb") as handle:
            self._classifier = pickle.load(handle)
        self._label_mapping = json.loads(
            (directory / "label_mapping.json").read_text(encoding="utf-8")
        )

    def classify(self, feedback_text: str) -> FeedbackResult:
        """Return a positive or negative reception signal for the feedback text.

        The text is vectorized and passed to the classifier; the predicted class
        index is mapped to a sentiment label through the trained label mapping.
        """
        features = self._vectorizer.transform([feedback_text])
        predicted = int(self._classifier.predict(features)[0])
        sentiment = self._label_mapping[str(predicted)]
        return FeedbackResult(
            feedback_text=feedback_text,
            sentiment=sentiment,
            model_name=MODEL_NAME,
        )
