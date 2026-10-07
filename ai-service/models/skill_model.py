from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier

def train_skill_classifier(X, y, random_state: int = 42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=200, random_state=random_state, class_weight="balanced"
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    return model, classification_report(y_test, predictions, output_dict=True)
