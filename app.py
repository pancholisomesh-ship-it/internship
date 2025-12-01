from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from ml_model import load_model
import joblib
import numpy as np
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time 
import matplotlib.pyplot as plt

graph_folder = os.path.join("static", "graphs")
os.makedirs(graph_folder, exist_ok=True)


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


# @app.route('/index')
# @login_required
# def index_page():
#     return render_template("index.html")


@app.route('/index')
@login_required
def index_page():
    if "monthly_income" not in session:
        return redirect("/income")
    return render_template("index.html")


# ---------------- INCOME PAGE ----------------
@app.route('/income')
@login_required
def income_page():
    return render_template("income.html")





# ---------------- REGISTER API ----------------
# @app.route('/register', methods=['POST'])
# def register():
#     data = request.get_json()

#     username = data.get("username")
#     password = data.get("password")

#     if not username or not password:
#         return jsonify({"error": "Missing fields"}), 400

#     if users_collection.find_one({"username": username}):
#         return jsonify({"error": "User already exists"}), 409

#     hashed = generate_password_hash(password)

#     users_collection.insert_one({
#         "username": username,
#         "password": hashed,
#         "is_admin": True


#     })

#     return jsonify({"message": "Registration successful","redirect":"/login"}), 201

@app.route('/register', methods=['POST'])
def register():
    data = request.json

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    is_admin = data.get('is_admin', False)   # <-- IMPORTANT
    hashed_password = generate_password_hash(password)


    user = {
        "username": username,
        "password": hashed_password,
        "email": email,
        "is_admin": True if is_admin == True else False   
    }
    users_collection.insert_one(user)
    return jsonify({"message": "Registered successfully","redirect":"/login"})





# ---------------- LOGIN API ----------------
# @app.route('/login', methods=['POST'])
# def login():
#     data = request.get_json()

#     username = data.get("username")
#     password = data.get("password")
#     email = data.get("email")

#     # --- FIND USER USING USERNAME + EMAIL BOTH ---
#     user_doc = users_collection.find_one({
#         "username": username,
#         "email": email
#     })

#     # --- USER DOES NOT EXIST ---
#     if not user_doc:
#         return jsonify({"error": "Invalid username or email"}), 401

#     # --- CHECK HASHED PASSWORD ---
#     if not check_password_hash(user_doc["password"], password):
#         return jsonify({"error": "Invalid password"}), 401

#     # --- LOGIN USER USING FLASK-LOGIN ---
#     user = User(user_doc)
#     login_user(user)

#     return jsonify({
#         "message": "Login successful",
#         "redirect": "/index"
#     }), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    # --- FIND USER ONLY BY USERNAME + EMAIL ---
    user = users_collection.find_one({
        "username": username,
        "email": email
    })

    # USER NOT FOUND
    if not user:
        return jsonify({"message": "Invalid username or email"}), 401

    # --- CHECK PLAIN PASSWORD DIRECTLY ---
    if not check_password_hash(user["password"], password):
         return jsonify({"error": "Invalid password"}), 401

    # SAVE SESSION
    session['user_id'] = str(user['_id'])
    session['is_admin'] = bool(user.get('is_admin', False))

    # LOGIN USER USING FLASK-LOGIN
    login_user(User(user))

    # REDIRECT BASED ON ADMIN
    if session['is_admin']:
        return jsonify({"message": "Admin login success", "redirect": "/admin"})
    else:
        return jsonify({"message": "User login success", "redirect": "/index"})



# ---------------- SAVE INCOME ----------------
@app.route('/save_income', methods=['POST'])
@login_required
def save_income():
    data = request.json
    income = float(data.get("income"))
    session["monthly_income"] = income
    return jsonify({"message": "Income saved", "redirect": "/index"})







# ---------------- LOGOUT ----------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# ---------------- ADMIN PAGE ----------------
# @app.route('/admin')
# @login_required
# def admin():
#     if not current_user.is_admin:
#         flash("Admin only!")
#         return redirect("/")

#     users = []
#     for u in users_collection.find({}):
#         users.append({
#             "id": str(u["_id"]),
#             "username": u["username"],
#             "is_admin": u.get("is_admin", False)
#         })

#     return render_template("admin.html", users=users)



# @app.route('/make_admin/<user_id>', methods=['POST'])

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return "Access denied: Only admin can open dashboard"
    return render_template('dashboard.html')

# @login_required
# def make_admin(user_id):
#     if not current_user.is_admin:
#         return jsonify({"error": "Unauthorized"}), 403

    # users_collection.update_one(
    #     {"_id": ObjectId(user_id)},
    #     {"$set": {"is_admin": True}}
    # )
    # return jsonify({"message": "User promoted to admin successfully"})



# ---------------- GRAPH + PREDICT ----------------
# @app.route('/predict', methods=['POST'])
# def predict():
#     if bill_model is None:
#         return jsonify({"error": "Model file missing"}), 500

#     data = request.get_json()
#     features = data.get("features")

#     if not features or len(features) != 8:
#         return jsonify({"error": "Need 8 features"}), 400

#     arr = np.array([features], dtype=float)
#     prediction = float(bill_model.predict(arr)[0])

#     # ----- GRAPH CODE -----
#     import matplotlib
#     matplotlib.use('Agg')
#     import matplotlib.pyplot as plt
#     import os

#     graph_folder = "static/graphs"
#     os.makedirs(graph_folder, exist_ok=True)

#     # 1. FEATURE GRAPH
#     plt.figure()
#     feature_names = [
#         "Kitchen Items", "Clothes", "Stationary", "Milk",
#         "Beautycare", "Health", "Electronic", "Grocery"
#     ]
#     plt.bar(feature_names, features)
#     plt.xticks(rotation=45)
#     plt.title("Input Features")
#     feature_graph_path = f"{graph_folder}/input_features.png"
#     plt.tight_layout()
#     plt.savefig(feature_graph_path)
#     plt.close()

#     # 2. PREDICTION GRAPH
#    # 2. PREDICTION GRAPH – PIE CHART
#     plt.figure()
#     plt.pie([prediction, 1000], labels=["Predicted Bill", ""], autopct="%1.1f%%")
#     plt.title("Predicted Bill Contribution")
#     prediction_graph_path = f"{graph_folder}/prediction_output.png"
#     plt.tight_layout()
#     plt.savefig(prediction_graph_path)
#     plt.close()


@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if bill_model is None:
        return jsonify({"error": "Model file missing"}), 500

    data = request.get_json()
    features = data.get("features")

    if not features or len(features) != 8:
        return jsonify({"error": "Need 8 features"}), 400

    arr = np.array([features], dtype=float)
    prediction = float(bill_model.predict(arr)[0])

    # income & savings
    income = session.get("monthly_income", 0)
    remaining = income - prediction

    # GRAPH
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import os

    graph_folder = "static/graphs"
    os.makedirs(graph_folder, exist_ok=True)

    # FEATURE GRAPH
    plt.figure()
    labels = ["Kitchen Items","Clothes","Stationary","Milk","Beautycare","Health","Electronic","Grocery"]
    plt.bar(labels, features)
    plt.xticks(rotation=45)
    plt.title("Input Features")
    plt.tight_layout()
    plt.savefig(f"{graph_folder}/input_features.png")
    plt.close()

    # PREDICTION GRAPH
    plt.figure()
    plt.pie(["Predicted Bill"], [prediction])
    plt.title("Predicted Bill Amount")
    plt.tight_layout()
    plt.savefig(f"{graph_folder}/prediction_output.png")
    plt.close()

    # ts = int(time.time())

    # return jsonify({
    #     "predicted_bill": prediction,
    #     "remaining_amount": remaining,
    #     "graphs": {
    #         "input_features": f"/static/graphs/input_features.png?t={ts}",
    #         "prediction_graph": f"/static/graphs/prediction_output.png?t={ts}"
    #     }
    # })






    ts = int(time.time())
    return jsonify({
            "predicted_bill": prediction,
            "remaining_amount": remaining,
            "graphs": {
                "input_features": f"/static/graphs/input_features.png?t={ts}",
                "prediction_graph": f"/static/graphs/prediction_output.png?t={ts}"
            }
        })





# ---------------- MAIN ----------------
# if __name__ == "__main__":
#     app.run(debug=True, use_reloader=False)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
