import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# Load your dataset
df = pd.read_csv("monthly expense.csv")


# df = pd.read_csv("monthly expense.csv", encoding="latin1", engine="python", on_bad_lines="skip")


# Columns in your dataset must match:
# ['Channel','Region','Fresh','Milk','Grocery','Frozen','Detergents_Paper','Delicassen']

# Create target variable: Total amount spent
df["Total_Bill"] = df["kitchenhomeitems"] + df["Milk"] + df["Grocery"] + df["clothes"] + df["Electronic"] + df["Stationary"] + df["Beautycares"] + df["Healthfitness"]

# Feature columns
X = df[['kitchenhomeitems','clothes','Electronic','Milk','Grocery','Stationary','Beautycares','Healthfitness']]
y = df["Total_Bill"]

# Train/Test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model
model = RandomForestRegressor(n_estimators=300, random_state=42)
model.fit(X_train, y_train)

# Predictions
preds = model.predict(X_test)

print("MAE:", mean_absolute_error(y_test, preds))
print("R² Score:", r2_score(y_test, preds))

# Save model
joblib.dump(model, "bill_predictor.joblib")

print("Model saved as bill_predictor.joblib")
def load_model():
    """Load the trained RandomForest model."""
    model = joblib.load("bill_predictor.joblib")
    return model