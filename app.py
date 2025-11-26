from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from ml_model import load_model
import joblib
import numpy as np
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------- App init ----------------
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ---------------- HARDCODED CONFIG ----------------
app.config['SECRET_KEY'] = "4f829c1abc9d9d1779ef3ecf3baab23a9adcee12df345acf90af1bcbf5e3288a"
app.config["MONGO_URI"] = "mongodb+srv://admin:root@cluster0.cvf0hfq.mongodb.net/someshji"

mongo = PyMongo(app)
users_collection = mongo.db.users

# ---------------- LOGIN MANAGER ----------------
login_manager = LoginManager()
login_manager.login_view = "login_page"
login_manager.init_app(app)

# ---------------- LOAD ML MODEL ----------------
try:
    bill_model = joblib.load("bill_predictor.joblib")
except:
    bill_model = None

try:
    scaler, kmeans = load_model()
except:
    scaler, kmeans = None, None


# ---------------- USER CLASS ----------------
class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc["_id"])
        self.username = user_doc["username"]
        self.is_admin = user_doc.get("is_admin", False)

    @staticmethod
    def get(user_id):
        try:
            user_doc = users_collection.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                return User(user_doc)
        except:
            pass
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# ---------------- ROUTES ----------------
@app.route('/')
def index():
    return render_template("login.html")


@app.route('/register', methods=['GET'])
def register_page():
    return render_template("register.html")


@app.route('/login', methods=['GET'])
def login_page():
    return render_template("login.html")


@app.route('/index')
@login_required
def index_page():
    return render_template("index.html")


# ---------------- REGISTER API ----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "User already exists"}), 409

    hashed = generate_password_hash(password)

    users_collection.insert_one({
        "username": username,
        "password": hashed,
        "is_admin": False
    })

    return jsonify({"message": "Registration successful","redirect":"/login"}), 201


# ---------------- LOGIN API ----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user_doc = users_collection.find_one({"username": username})

    if not user_doc or not check_password_hash(user_doc["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    user = User(user_doc)
    login_user(user)

    return jsonify({"message": "Login successful", "redirect": "/index"}), 200


# ---------------- LOGOUT ----------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# ---------------- ADMIN PAGE ----------------
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash("Admin only!")
        return redirect("/")

    users = []
    for u in users_collection.find({}):
        users.append({
            "id": str(u["_id"]),
            "username": u["username"],
            "is_admin": u.get("is_admin", False)
        })

    return render_template("admin.html", users=users)


# ---------------- PREDICT API ----------------
@app.route('/predict', methods=['POST'])
def predict():
    if bill_model is None:
        return jsonify({"error": "Model file missing"}), 500

    data = request.get_json()
    features = data.get("features")

    if not features or len(features) != 8:
        return jsonify({"error": "Need 8 features"}), 400

    arr = np.array([features], dtype=float)
    prediction = float(bill_model.predict(arr)[0])

    return jsonify({"predicted_bill": prediction})


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
