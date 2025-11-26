import joblib
import numpy as np

# Load saved model
model = joblib.load("bill_predictor.joblib")

def predict_bill(kitchenhomeitems, clothes, Stationary, Milk, Grocery, Beautycares, Healthfitness, Electronic):
    features = np.array([[kitchenhomeitems, clothes, Stationary, Milk, Beautycares, Healthfitness, Electronic, Grocery]])
    total_bill = model.predict(features)[0]
    return total_bill

# Example usage:
example_bill = predict_bill(1, 3, 2000, 1500, 3000, 500, 800, 600)
print("Predicted Total Bill:", example_bill)
