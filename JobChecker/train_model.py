"""
Trains the baseline ML classifier described in SRS section 5.1-B:
"a supervised model (e.g., Random Forest, XGBoost, or a fine-tuned
transformer-based classifier) trained on the extracted features to output a
fraud-probability score."

Here we use TF-IDF features + Logistic Regression: lightweight, fast to
train, and easy to explain -- a reasonable baseline for a prototype. Swap in
a stronger model later (e.g., a fine-tuned transformer) without changing the
rest of the pipeline, since app/classifier.py only depends on
predict_proba().
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"


def main():
    MODEL_DIR.mkdir(exist_ok=True)

    csv_path = DATA_DIR / "training_data.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Run `python data/generate_data.py` first "
            "(or supply your own labeled dataset with 'text' and 'label' columns)."
        )

    df = pd.read_csv(csv_path)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), stop_words="english")
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train_vec, y_train)

    preds = model.predict(X_test_vec)
    print(classification_report(y_test, preds, target_names=["legit", "scam"]))

    joblib.dump(model, MODEL_DIR / "classifier.joblib")
    joblib.dump(vectorizer, MODEL_DIR / "vectorizer.joblib")
    print(f"Saved model and vectorizer to {MODEL_DIR}")


if __name__ == "__main__":
    main()
