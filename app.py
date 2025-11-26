# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from ml_model import load_model
import os
from flask_cors import CORS
import joblib
import numpy as np

bill_model = joblib.load("bill_predictor.joblib")

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = '4f829c1abc9d9d1779ef3ecf3baab23a9adcee12df345acf90af1bcbf5e3288a'

# -----------------------------
# 🔥 MONGODB ATLAS CONFIG HERE
# -----------------------------
app.config["MONGO_URI"] = "mongodb+srv://admin:root@cluster0.cvf0hfq.mongodb.net/someshji"
mongo = PyMongo(app)

users_collection = mongo.db.users   # acts like a table
# -----------------------------

login_manager = LoginManager()
login_manager.init_app(app)

try:
    scaler, kmeans = load_model()
except:
    scaler, kmeans = None, None


# 🔥 Custom user loader (MongoDB)
@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        user['id'] = str(user['_id'])
    return user


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template("register.html")

@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/index')
def index_page():
    return render_template("index.html")





# ---------------- REGISTER ----------------
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()   # Receive JSON from frontend

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    # Check if user exists
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409

    # Insert user
    users_collection.insert_one({
        "username": username,
        "password": password,
        "is_admin": False
    })

    return jsonify({"message": "Registration successful", "redirect": "/"}), 201


# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()        # Receive JSON

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    username = data.get("username")
    password = data.get("password")

    # Validate
    user = users_collection.find_one({"username": username, "password": password})

    if user:
        session['username'] = username
        return jsonify({"message": "Login successful", "redirect": "/index"}), 200

    return jsonify({"error": "Invalid username or password"}), 401


# ---------------- LOGOUT ----------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ---------------- ADMIN PAGE ----------------
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash("Admin access only!")
        return redirect(url_for('index'))

    users = users_collection.query.all()
    return render_template('admin.html', users=users)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()

    if not data or 'features' not in data:
        return jsonify({"error": "Invalid input"}), 400

    values = data['features']

    if len(values) != 8:
        return jsonify({"error": "Need 8 features"}), 400

    values = np.array([values])
    total_bill = float(bill_model.predict(values)[0])

    return jsonify({"predicted_bill": total_bill})




# ---------------- RUN FLASK APP ----------------
if __name__ == '__main__':
    app.run(debug=True)
