import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn import metrics
import joblib
import os

# 1. Load the data
df = pd.read_csv('../data/products.csv')

# 2. Prepare the data
X = df['product_name']
y = df['category']

# 3. Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 4. Build the model pipeline
model = make_pipeline(
    TfidfVectorizer(),
    LogisticRegression(max_iter=1000)
)

# 5. Train the model
model.fit(X_train, y_train)

# 6. Evaluate
y_pred = model.predict(X_test)
accuracy = metrics.accuracy_score(y_test, y_pred)
print(f"✅ Classifier accuracy on test set: {accuracy * 100:.2f}%")

# 7. Save the trained model
os.makedirs('saved_models', exist_ok=True)
joblib.dump(model, 'saved_models/product_category_classifier.joblib')
print("✅ Model saved to saved_models/product_category_classifier.joblib")
