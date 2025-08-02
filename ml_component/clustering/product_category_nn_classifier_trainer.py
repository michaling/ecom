import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn import metrics
import joblib
from ml_component.globals import *
import os

response = supabase.table('model_products').select('product_name, category_name').execute()
data = response.data
df = pd.DataFrame(data)
X = df['product_name']
y = df['category_name']

# Assume X, y are already fetched as shown above
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = make_pipeline(
    TfidfVectorizer(),
    MLPClassifier(hidden_layer_sizes=(100,), max_iter=300, random_state=42)
)

model.fit(X_train, y_train)
y_pred = model.predict(X_test)
accuracy = metrics.accuracy_score(y_test, y_pred)
print(f"MLP Classifier accuracy: {accuracy * 100:.2f}%")

os.makedirs('saved_models', exist_ok=True)
joblib.dump(model, 'saved_models/product_category_classifier_nn.joblib')
print("Model saved")
