from pathlib import Path
from openpyxl import load_workbook
import math
import json
import random

RAW = Path("data/raw")
OUT = Path("data/evaluation")
OUT.mkdir(parents=True, exist_ok=True)

random.seed(42)


def load_excel(filename):
    wb = load_workbook(RAW / filename, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.values)
    wb.close()

    headers = [str(x).strip() if x is not None else "" for x in rows[0]]
    return [
        dict(zip(headers, row))
        for row in rows[1:]
    ]


def sigmoid(z):
    z = max(-500, min(500, z))
    return 1 / (1 + math.exp(-z))


def train_logistic(X, y, epochs=1500, lr=0.05):
    n = len(X)
    m = len(X[0])

    means = [
        sum(row[j] for row in X) / n
        for j in range(m)
    ]

    stds = []

    for j in range(m):
        variance = sum(
            (row[j] - means[j]) ** 2
            for row in X
        ) / n

        stds.append(math.sqrt(variance) or 1)

    Xs = [
        [(row[j] - means[j]) / stds[j] for j in range(m)]
        for row in X
    ]

    weights = [0.0] * m
    bias = 0.0

    for _ in range(epochs):
        grad_w = [0.0] * m
        grad_b = 0.0

        for row, target in zip(Xs, y):
            probability = sigmoid(
                sum(w * x for w, x in zip(weights, row)) + bias
            )

            error = probability - target

            for j in range(m):
                grad_w[j] += error * row[j]

            grad_b += error

        for j in range(m):
            weights[j] -= lr * grad_w[j] / n

        bias -= lr * grad_b / n

    return weights, bias, means, stds


def predict(X, model):
    weights, bias, means, stds = model

    predictions = []

    for row in X:
        scaled = [
            (row[j] - means[j]) / stds[j]
            for j in range(len(row))
        ]

        probability = sigmoid(
            sum(w * x for w, x in zip(weights, scaled)) + bias
        )

        predictions.append(1 if probability >= 0.5 else 0)

    return predictions


def metrics(y_true, y_pred):
    tp = sum(a == 1 and b == 1 for a, b in zip(y_true, y_pred))
    tn = sum(a == 0 and b == 0 for a, b in zip(y_true, y_pred))
    fp = sum(a == 0 and b == 1 for a, b in zip(y_true, y_pred))
    fn = sum(a == 1 and b == 0 for a, b in zip(y_true, y_pred))

    accuracy = (tp + tn) / len(y_true)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0
    )

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion_matrix": [
            [tn, fp],
            [fn, tp]
        ]
    }


def run_model(filename, features, target, dataset_name):

    rows = load_excel(filename)

    X = []
    y = []

    for row in rows:
        try:
            values = [
                float(row[f])
                for f in features
            ]

            label = int(row[target])

            if all(math.isfinite(v) for v in values):
                X.append(values)
                y.append(label)

        except (TypeError, ValueError, KeyError):
            continue

    combined = list(zip(X, y))
    random.shuffle(combined)

    X, y = zip(*combined)

    X = list(X)
    y = list(y)

    split = int(len(X) * 0.75)

    X_train = X[:split]
    y_train = y[:split]

    X_test = X[split:]
    y_test = y[split:]

    model = train_logistic(X_train, y_train)

    predictions = predict(X_test, model)

    result = metrics(y_test, predictions)

    print("\n" + "=" * 80)
    print(dataset_name)
    print("=" * 80)

    print("Complete records:", len(X))
    print("Training records:", len(X_train))
    print("Testing records :", len(X_test))

    print("\nLogistic Regression-style classifier")
    print("-------------------------------------")

    print("Accuracy :", result["accuracy"])
    print("Precision:", result["precision"])
    print("Recall   :", result["recall"])
    print("F1 Score :", result["f1"])

    print("\nConfusion Matrix:")
    print(result["confusion_matrix"])

    print("\nFeature coefficients:")

    weights = model[0]

    ranked = sorted(
        zip(features, weights),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    for feature, weight in ranked:
        print(f"{feature}: {weight:.4f}")

    result["dataset"] = dataset_name
    result["features"] = features

    return result


# ============================================================
# SKILL MODEL
# ============================================================

skill_features = [
    "big_data_skills",
    "maths-stats_skills",
    "coding_skills",
    "ai_and_ml_skills",
    "dashboard_and_storytelling_skills"
]

skill_result = run_model(
    "JDS Skill Traits.xlsx",
    skill_features,
    "salary_hike_high_or_low",
    "Technical Skills → Salary Hike"
)


# ============================================================
# PERSONALITY MODEL
# ============================================================

personality_features = [
    "neuroticism",
    "extraversion",
    "openness_to_experience",
    "agreeableness",
    "conscientiousness"
]

personality_result = run_model(
    "SDS Personality Traits.xlsx",
    personality_features,
    "success_ classification_ high_low",
    "Personality → Success"
)


# ============================================================
# SAVE
# ============================================================

results = [
    skill_result,
    personality_result
]

with open(
    OUT / "ml_results.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 80)
print("ML ANALYSIS COMPLETE")
print("=" * 80)
print("Saved to:", OUT / "ml_results.json")
