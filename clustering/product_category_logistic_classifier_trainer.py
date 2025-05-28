import os
import pandas as pd
from supabase import create_client
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn import metrics
import joblib

# --- Supabase credentials ---
SUPABASE_URL = "https://nallltanfjxhuaxvlwaf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5hbGxsdGFuZmp4aHVheHZsd2FmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3NTA5NzAsImV4cCI6MjA2MTMyNjk3MH0.QJi8v8eKu2QOEGPyRbgGL7Yaaj3zj22Mi8PEDz6WcbE"

# --- Supabase initialization ---
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Fetch product data ---
response = supabase.table("model_products").select("product_name, category_name").execute()
records = response.data
df = pd.DataFrame(records)

# --- Validate ---
if df.empty or 'product_name' not in df.columns or 'category_name' not in df.columns:
    raise ValueError("Supabase must return 'product_name' and 'category_name' columns.")

# --- Prepare data ---
X = df['product_name']
y = df['category_name']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- Build model ---
model = make_pipeline(
    TfidfVectorizer(),
    LogisticRegression(max_iter=1000)
)

# --- Train ---
model.fit(X_train, y_train)

# --- Evaluate ---
y_pred = model.predict(X_test)
accuracy = metrics.accuracy_score(y_test, y_pred)
print(f"✅ Logistic classifier accuracy: {accuracy * 100:.2f}%")

# --- Save ---
os.makedirs('saved_models', exist_ok=True)
joblib.dump(model, 'saved_models/product_category_classifier.joblib')
print("✅ Model saved to saved_models/product_category_classifier.joblib")
