"""
Model Training Script — Train ML models to predict optimal task scheduling.

Trains multiple classifiers (RandomForest, GradientBoosting, XGBoost)
and selects the best performing model based on cross-validation accuracy.

The trained model is saved as model.pkl for use by the ML Engine service.

Usage:
    python -m ml.train_model

Algorithm overview:
    - Target: optimal_hour (0-23) — when the user actually completes tasks
    - Features: priority, duration, category, day_of_week, cyclical time encodings
    - Selection: best model from RF, GBM, XGB based on cross-validation score
    - Output: model artifact (model.pkl) with metadata
"""

import os
import warnings
import json
from datetime import datetime

import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler

# Optional: XGBoost (falls back to GBM if not installed)
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("⚠️  XGBoost not installed — using GradientBoosting as fallback")

from ml.preprocessing import preprocess_pipeline

warnings.filterwarnings("ignore")

# ── Configuration ──────────────────────────────────────────────────────────
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
RANDOM_STATE = 42
CV_FOLDS = 5


def build_models():
    """
    Create a dictionary of candidate models to train and evaluate.

    Each model is a scikit-learn compatible classifier.
    """
    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=RANDOM_STATE,
        ),
    }

    if HAS_XGBOOST:
        models["XGBoost"] = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=RANDOM_STATE,
            use_label_encoder=False,
            eval_metric="mlogloss",
            verbosity=0,
        )

    return models


def train_and_evaluate(X, y, feature_names):
    """
    Train all candidate models, evaluate via cross-validation,
    and select the best performer.

    Steps:
        1. Split data into train/test sets (80/20)
        2. Scale features with StandardScaler
        3. Train each model with cross-validation
        4. Evaluate on held-out test set
        5. Return the best model with metadata

    Args:
        X: Feature matrix
        y: Target vector (optimal hours)
        feature_names: List of feature column names

    Returns:
        Dictionary with best model, accuracy, and metadata
    """
    print("\n" + "=" * 60)
    print("🤖 MODEL TRAINING PIPELINE")
    print("=" * 60)

    # ── Train/Test Split ───────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=None
    )
    print(f"\n📊 Train samples: {len(X_train)}, Test samples: {len(X_test)}")

    # ── Feature Scaling ────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ── Train and Evaluate Each Model ──────────────────────────────
    models = build_models()
    results = {}

    for name, model in models.items():
        print(f"\n{'─' * 40}")
        print(f"🔄 Training: {name}")

        # Cross-validation on training set
        cv_scores = cross_val_score(
            model, X_train_scaled, y_train,
            cv=min(CV_FOLDS, len(X_train)),
            scoring="accuracy",
        )
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()
        print(f"   CV Accuracy: {cv_mean:.4f} ± {cv_std:.4f}")

        # Train on full training set
        model.fit(X_train_scaled, y_train)

        # Evaluate on test set
        y_pred = model.predict(X_test_scaled)
        test_accuracy = accuracy_score(y_test, y_pred)
        print(f"   Test Accuracy: {test_accuracy:.4f}")

        # Feature importance (for tree-based models)
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            top_features = sorted(
                zip(feature_names, importances),
                key=lambda x: x[1], reverse=True
            )[:5]
            print(f"   Top features: {[(f, f'{i:.3f}') for f, i in top_features]}")

        results[name] = {
            "model": model,
            "cv_accuracy": cv_mean,
            "cv_std": cv_std,
            "test_accuracy": test_accuracy,
        }

    # ── Select Best Model ──────────────────────────────────────────
    best_name = max(results, key=lambda k: results[k]["test_accuracy"])
    best_result = results[best_name]

    print(f"\n{'=' * 60}")
    print(f"🏆 Best Model: {best_name}")
    print(f"   Test Accuracy: {best_result['test_accuracy']:.4f}")
    print(f"   CV Accuracy: {best_result['cv_accuracy']:.4f} ± {best_result['cv_std']:.4f}")
    print(f"{'=' * 60}")

    # ── Detailed Classification Report ─────────────────────────────
    y_pred = best_result["model"].predict(X_test_scaled)
    print(f"\n📋 Classification Report ({best_name}):")
    print(classification_report(y_test, y_pred, zero_division=0))

    return {
        "model": best_result["model"],
        "scaler": scaler,
        "accuracy": best_result["test_accuracy"],
        "cv_accuracy": best_result["cv_accuracy"],
        "model_name": best_name,
        "feature_names": feature_names,
        "trained_at": datetime.utcnow().isoformat(),
        "all_results": {
            name: {
                "cv_accuracy": r["cv_accuracy"],
                "test_accuracy": r["test_accuracy"],
            }
            for name, r in results.items()
        },
    }


def save_model(model_data: dict, path: str = None):
    """
    Save the trained model and metadata to disk.

    Args:
        model_data: Dictionary containing model, scaler, and metadata
        path: File path for saving (default: ml/model.pkl)
    """
    if path is None:
        path = MODEL_PATH

    joblib.dump(model_data, path)
    print(f"\n💾 Model saved to: {path}")

    # Also save a human-readable summary
    summary_path = path.replace(".pkl", "_summary.json")
    summary = {
        "model_name": model_data["model_name"],
        "accuracy": model_data["accuracy"],
        "cv_accuracy": model_data["cv_accuracy"],
        "feature_names": model_data["feature_names"],
        "trained_at": model_data["trained_at"],
        "all_results": model_data["all_results"],
    }
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"📄 Summary saved to: {summary_path}")


def main():
    """
    Full training pipeline:
        1. Preprocess data (load → clean → feature extraction)
        2. Train multiple models with cross-validation
        3. Select and save the best model
    """
    print("🚀 Starting model training pipeline...\n")

    # Step 1: Preprocess
    X, y, feature_names, df = preprocess_pipeline()

    # Step 2: Train and evaluate
    model_data = train_and_evaluate(X, y, feature_names)

    # Step 3: Save best model
    save_model(model_data)

    print("\n✅ Training pipeline complete!")
    return model_data


if __name__ == "__main__":
    main()
