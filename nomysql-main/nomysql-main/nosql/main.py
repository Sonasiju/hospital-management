from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime

# App configuration
import os
app = Flask(__name__, static_folder='static')
app.secret_key = 'mehere'

# MongoDB connection
from flask_pymongo import PyMongo

app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)


mongo = PyMongo(app)

# Login manager setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        self.role = user_data.get('role')
        self.email = user_data.get('email')
        self.password = user_data.get('password')

    @staticmethod
    def get(user_id):
        user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(user_data)
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/doctors", methods=["POST", "GET"])
@login_required
def doctors():
    if current_user.role != 'Doctor':
        flash("Access restricted to doctors only", "danger")
        return redirect(url_for('index'))

    # Check if doctor already exists
    already_registered = mongo.db.doctors.find_one({"email": current_user.email}) is not None

    if already_registered:
        flash("You have already registered your specialization", "info")
        return redirect(url_for('index'))

    if request.method == "POST":
        email = request.form.get('email')
        doctorsname = request.form.get('doctorsname')
        dept = request.form.get('dept')

        # Validate all fields are filled
        if not all([email, doctorsname, dept]):
            flash("All fields are required!", "warning")
            return render_template('doctors.html')

        # Double-check doctor doesn't exist (prevent race condition)
        if mongo.db.doctors.find_one({"email": current_user.email}):
            flash("You have already registered your specialization", "info")
            return redirect(url_for('index'))

        doctor_data = {
            "email": email,
            "doctorsname": doctorsname,
            "dept": dept,
            "registered_at": datetime.now()
        }
        
        mongo.db.doctors.insert_one(doctor_data)
        flash("Specialization registered successfully", "success")
        return redirect(url_for('index'))

    return render_template('doctors.html', already_registered=already_registered)

@app.route("/patients", methods=["POST", "GET"])
@login_required
def patients():
    # Get all departments from doctors
    departments = mongo.db.doctors.distinct("dept")
    
    if request.method == "POST":
        email = request.form.get('email')
        name = request.form.get('name')
        gender = request.form.get('gender')
        slot = request.form.get('slot')
        disease = request.form.get('disease')
        time = request.form.get('time')
        date = request.form.get('date')
        dept = request.form.get('dept')
        doctor_email = request.form.get('doctor_email')
        number = request.form.get('number')

        if len(number) != 10:
            flash("Please provide a 10 digit phone number", "warning")
            return render_template('patients.html', departments=departments)

        patient_data = {
            "email": email,
            "name": name,
            "gender": gender,
            "slot": slot,
            "disease": disease,
            "time": time,
            "date": date,
            "dept": dept,
            "doctor_email": doctor_email,
            "number": number,
            "created_at": datetime.now()
        }
        
        mongo.db.patients.insert_one(patient_data)
        flash("Booking Confirmed", "success")
        return redirect(url_for('bookings'))

    return render_template('patients.html', departments=departments)

@app.route('/get_doctors/<department>')
def get_doctors(department):
    doctors = list(mongo.db.doctors.find({"dept": department}, {"email": 1, "doctorsname": 1, "_id": 0}))
    return {"doctors": doctors}


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = mongo.db.users.find_one({"email": email})
        
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            flash("Login Success ✪ ω ✪", "info")
            return render_template('base.html')
        else:
            flash("INVALID CREDENTIALS ┬┬﹏┬┬", "danger")
            return render_template('login.html')
    
    return render_template('login.html')
@app.route('/bookings')
@login_required
def bookings():
    # Check if user is doctor and has registered specialization
    is_doctor_registered = False
    if current_user.role == "Doctor":
        is_doctor_registered = mongo.db.doctors.find_one({"email": current_user.email}) is not None

    if current_user.role == "Doctor":
        pipeline = [
            {"$match": {"doctor_email": current_user.email}},
            {"$lookup": {
                "from": "doctors",
                "localField": "doctor_email",
                "foreignField": "email",
                "as": "doctor_info"
            }},
            {"$unwind": {"path": "$doctor_info", "preserveNullAndEmptyArrays": True}}
        ]
    else:
        pipeline = [
            {"$match": {"email": current_user.email}},
            {"$lookup": {
                "from": "doctors",
                "localField": "doctor_email",
                "foreignField": "email",
                "as": "doctor_info"
            }},
            {"$unwind": {"path": "$doctor_info", "preserveNullAndEmptyArrays": True}},
            {"$addFields": {
                "doctor_name": {"$ifNull": ["$doctor_info.doctorsname", "Doctor not found"]}
            }}
        ]
    
    query = list(mongo.db.patients.aggregate(pipeline))
    return render_template('bookings.html', 
                         query=query,
                         is_doctor_registered=is_doctor_registered,
                         current_user=current_user)  # Pass current_user to template





@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout successful (∪.∪ )...zzz", "primary")
    return redirect(url_for('index'))

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = mongo.db.users.find_one({"email": email})
        if existing_user:
            flash("Email Already Exists...(⊙_⊙)？", "warning")
            return render_template('/signup.html')
        
        encpassword = generate_password_hash(password)
        user_data = {
            "username": username,
            "role": role,
            "email": email,
            "password": encpassword
        }
        
        mongo.db.users.insert_one(user_data)
        flash("Signup Success ￣︶￣　 Please Login ◕.◕", "success")
        return render_template('login.html')
    
    return render_template('signup.html')


@app.route("/test")
def test():
    try:
        mongo.db.test.find_one()
        return 'db connected'
    except Exception as e:
        return f'db not connected: {str(e)}'

@app.route("/edit/<patient_id>", methods=["POST", "GET"])
@login_required
def edit(patient_id):
    # Get all departments first
    departments = mongo.db.doctors.distinct("dept")
    
    # Get the patient record
    post = mongo.db.patients.find_one({"_id": ObjectId(patient_id)})
    
    if not post:
        flash("Patient not found", "danger")
        return redirect(url_for('bookings'))
    
    # Get the doctor's name
    doctor = mongo.db.doctors.find_one({"email": post.get("doctor_email")})
    doctor_name = doctor.get("doctorsname") if doctor else "Doctor not found"

    if request.method == "POST":
        email = request.form.get('email')
        name = request.form.get('name')
        gender = request.form.get('gender')
        slot = request.form.get('slot')
        disease = request.form.get('disease')
        time = request.form.get('time')
        date = request.form.get('date')
        dept = request.form.get('dept')
        doctor_email = request.form.get('doctor_email')
        number = request.form.get('number')

        update_data = {
            "email": email,
            "name": name,
            "gender": gender,
            "slot": slot,
            "disease": disease,
            "time": time,
            "date": date,
            "dept": dept,
            "doctor_email": doctor_email,
            "number": number
        }
        
        result = mongo.db.patients.update_one(
            {"_id": ObjectId(patient_id)},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            flash("Booking updated successfully", "success")
        else:
            flash("No changes made", "info")
        return redirect(url_for('bookings'))

    return render_template('edit.html', 
                         posts=post, 
                         departments=departments,
                         doctor_name=doctor_name)

@app.route("/delete/<patient_id>", methods=["POST", "GET"])
@login_required
def delete(patient_id):
    result = mongo.db.patients.delete_one({"_id": ObjectId(patient_id)})
    if result.deleted_count > 0:
        flash("Slot Deleted Successfully", "danger")
    else:
        flash("Patient not found", "danger")
    return redirect(url_for('bookings'))

@app.route('/details')
@login_required
def details():
    # In MongoDB we'll track changes in a separate collection for triggers 
    # since MongoDB doesn't have triggers like relational databases
    posts = list(mongo.db.triggers.find().sort("timestamp", -1))
    return render_template('trigers.html', posts=posts)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == "POST":
        query = request.form.get('search', '').strip()
        
        if not query:
            flash("Please enter a search term", "warning")
            return redirect(url_for('index'))
        
        # Search in both department and doctor names
        doctors = list(mongo.db.doctors.find({
            "$or": [
                {"dept": {"$regex": query, "$options": "i"}},
                {"doctorsname": {"$regex": query, "$options": "i"}}
            ]
        }))
        
        if doctors:
            doctor_names = ", ".join([d['doctorsname'] for d in doctors])
            flash(f"Found {len(doctors)} doctor(s): {doctor_names}", "success")
        else:
            flash("No doctors found matching your search", "danger")
        
        return redirect(url_for('index'))
    
    return redirect(url_for('index'))

# Implement a function to track changes (mimicking triggers)
def log_patient_change(patient_id, email, action):
    trigger_data = {
        "patient_id": patient_id,
        "email": email,
        "action": action,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    mongo.db.triggers.insert_one(trigger_data)


@app.before_first_request
def initialize_indexes():
    if mongo.db is not None:
   
        mongo.db.prescriptions.create_index([("patient_id", 1)])
        mongo.db.prescriptions.create_index([("doctor_email", 1)])
        mongo.db.prescriptions.create_index([("date_prescribed", -1)])
    else:
        print("MongoDB is not connected properly.")


if __name__ == "__main__":
    app.run(debug=True)
