import pandas as pd
import matplotlib.pyplot as plt
import warnings
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay, matthews_corrcoef, \
    roc_auc_score, roc_curve
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier, BaggingClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

from sklearn.model_selection import cross_val_score, RandomizedSearchCV

from sklearn.preprocessing import LabelEncoder

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

warnings.filterwarnings('ignore')
data = pd.read_csv("dataset/phishing.csv")

label_encoder = LabelEncoder()

data["status"] = label_encoder.fit_transform(data["status"])

X = data.drop(["url", "status"], axis=1)
y = data["status"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=True)


def base_models(X, y, scoring="accuracy"):
    models = {"Random Forest": RandomForestClassifier(), "Decision Tree": DecisionTreeClassifier(),
              "Gradient Boosting": GradientBoostingClassifier(), "SVM": SVC(),
              "ADA Boost": AdaBoostClassifier(), "Bagging Classifier": BaggingClassifier(),
              "Naive Bayes": GaussianNB(), "XGBoost": XGBClassifier(),
              "Light-GBM": LGBMClassifier(verbose=-1),
              }
    for name, model in models.items():
        cv_scores = cross_val_score(model, X, y, cv=5, scoring=scoring, n_jobs=-1)
        print(f"{name} {scoring} score: {cv_scores.mean()}")


base_models(X_train, y_train)

params = {
    'n_estimators': [200, 400, 500, 750, 100],
    'criterion': ['gini', 'entropy'],
    'max_depth': [None, 10, 20, 30],
    'bootstrap': [True, False]
}

model = RandomForestClassifier()

random_search = RandomizedSearchCV(model, param_distributions=params, n_iter=10, n_jobs=-1, cv=3)
random_search.fit(X_train, y_train)

best_params = random_search.best_params_
print("Best parameters:", best_params)

best_model = RandomForestClassifier(**best_params)

best_model.fit(X_train, y_train)
predictions = best_model.predict(X_test)

print(classification_report(y_test, predictions))

cm = confusion_matrix(y_test, predictions)

plt.figure()
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=best_model.classes_)
disp.plot(cmap='viridis')
plt.title('Confusion Matrix')
# plt.savefig("images/confision_matrix")
# plt.show()

probs = best_model.predict_proba(X_test)[:, 1]
fpr, tpr, thresholds = roc_curve(y_test, probs)
roc_auc = roc_auc_score(y_test, probs)

plt.plot(fpr, tpr, lw=2)
plt.plot([0, 1], [0, 1], lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
# plt.savefig("images/roc-auc_curve")
# plt.show()


def plot_feature_importance(model, feature_names, plot=False):
    feature_importances = model.feature_importances_
    feature_importance_dict = dict(zip(feature_names, feature_importances))
    sorted_feature_importance = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)
    sorted_feature_names, sorted_feature_importances = zip(*sorted_feature_importance)
    feature_importance_df = pd.DataFrame({'Feature': sorted_feature_names, 'Importance': sorted_feature_importances})
    if plot:
        plt.figure(figsize=(30, 30))
        plt.barh(sorted_feature_names, sorted_feature_importances)
        plt.xlabel('Importance')
        plt.ylabel('Feature')
        plt.title('Feature Importance')
        plt.gca().invert_yaxis()
        # plt.savefig("images/feature_importance")
        # plt.show()
    return feature_importance_df

plot_feature_importance(best_model, X.columns, plot=True)
joblib.dump(best_model, "model/phishing.pkl")

