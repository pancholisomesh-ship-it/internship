# train_model.py
from ml_model import train_and_save_model
CSV_PATH = 'Monthly expense data.csv'


if __name__ == '__main__':
    print("Training model from:", CSV_PATH)
    scaler, kmeans = train_and_save_model(CSV_PATH, n_clusters=6)
    print("Saved scaler and kmeans.")