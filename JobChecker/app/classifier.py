"""
ML classifier wrapper.

Uses XGBoost (gradient-boosted decision trees). Gradient boosting can capture non-linear
interactions between red-flag terms that a purely linear model
tends to miss, making it a better fit as the scam-detection vocabulary
grows more varied.

Trains (or loads a cached) TF-IDF
vectorizer + XGBoost model directly from data/training_data.csv, and saves
both under the SAME filenames the rest of the app already expects
(models/classifier.joblib, models/vectorizer.joblib). knowledge_base.py's
RAG retrieval loads models/vectorizer.joblib too, so it automatically keeps
using the same embedding space.
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

_CLASSIFIER_PATH = MODEL_DIR / "classifier.joblib"
_VECTORIZER_PATH = MODEL_DIR / "vectorizer.joblib"
_TRAINING_DATA_PATH = DATA_DIR / "training_data.csv"


class ScamClassifier:
    def __init__(self, force_retrain: bool = False):
        MODEL_DIR.mkdir(exist_ok=True)

        if not force_retrain and _CLASSIFIER_PATH.exists() and _VECTORIZER_PATH.exists():
            self.model = joblib.load(_CLASSIFIER_PATH)
            self.vectorizer = joblib.load(_VECTORIZER_PATH)
        else:
            self.model, self.vectorizer = self._train_and_save()

        self._classes = list(self.model.classes_)

    def _train_and_save(self):
        if not _TRAINING_DATA_PATH.exists():
            raise FileNotFoundError(
                f"{_TRAINING_DATA_PATH} not found. Run `python data/generate_data.py` "
                "first (or supply your own labeled 'text'/'label' CSV)."
            )

        df = pd.read_csv(_TRAINING_DATA_PATH)
        X_train, X_test, y_train, y_test = train_test_split(
            df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
        )

        vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)

        model = XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=42,
        )
        model.fit(X_train_vec, y_train)

        test_acc = model.score(X_test_vec, y_test)
        print(f"[classifier.py] XGBoost classifier trained. Held-out accuracy: {test_acc:.3f}")

        joblib.dump(model, _CLASSIFIER_PATH)
        joblib.dump(vectorizer, _VECTORIZER_PATH)
        return model, vectorizer

    def predict_proba(self, text: str) -> float:
        """Return the probability (0-1) that the given text is a scam posting."""
        X = self.vectorizer.transform([text])
        proba = self.model.predict_proba(X)[0]
        idx = self._classes.index(1)  # class 1 = scam
        return float(proba[idx])
