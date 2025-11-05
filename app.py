import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from functools import wraps

# --- Firebase and Firestore Imports ---
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. CONFIGURATION AND INITIALIZATION ---
app = Flask(__name__)

# Secret key for sessions and flash messages
app.secret_key = 'YOUR_SECURE_RANDOM_KEY_987654123'

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# --- 2. FIREBASE INITIALIZATION ---
try:
    # Path to service account JSON key
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tech-it-2025-dc06080d93ae.json")

    if not firebase_admin._apps:
        cred = credentials.Certificate(json_path)
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    print("✅ Firestore connected successfully.")

except Exception as e:
    print(f"❌ ERROR: Firebase/Firestore initialization failed: {e}")
    db = None

# Firestore collection name
USERS_COLLECTION = "users"


# --- 3. AUTH DECORATOR (FOR PROTECTED ROUTES) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("You must be logged in to view that page.", 'warning')
            return redirect(url_for('handle_login'))
        return f(*args, **kwargs)
    return decorated_function


# --- 4. STANDARD ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/courses')
@login_required
def courses():
    return render_template('courses.html')

@app.route('/jobs')
@login_required
def jobs():
    return render_template('jobs.html')

@app.route('/search_results', methods=['GET', 'POST'])
def search_results():
    return redirect(url_for('index'))


# --- 5. LOGIN ROUTE ---
@app.route('/login', methods=['GET', 'POST'])
def handle_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Safety check
        if not db:
            flash("System Error: Database connection failed.", 'error')
            return render_template('login.html')

        # 1️⃣ Try to find user by email
        user_doc = db.collection(USERS_COLLECTION).document(email).get()
        user_data = None

        if not user_doc.exists:
            # Fallback search (in case email isn’t document ID)
            users_ref = db.collection(USERS_COLLECTION)
            query = users_ref.where("email", "==", email).limit(1).stream()
            for doc in query:
                user_data = doc.to_dict()
                break
        else:
            user_data = user_doc.to_dict()

        # 2️⃣ Check user existence
        if not user_data:
            flash("Invalid password or Email.", 'error')
            return render_template('login.html')

        # 3️⃣ Verify password
        stored_hash = user_data.get('password')
        if stored_hash and bcrypt.check_password_hash(stored_hash, password):
            session['logged_in'] = True
            session['user_email'] = email
            session['user_name'] = user_data.get('first_name', 'User')
            flash(f"Welcome back, {session['user_name']}!", 'success')
            return redirect(url_for('index'))
        else:
            flash("Invalid password or Email.", 'error')

    return render_template('login.html')


# --- 6. SIGNUP ROUTE ---
@app.route('/signup', methods=['GET', 'POST'])
def handle_signup():
    if request.method == 'POST':
        first_name = request.form.get('First_name')
        last_name = request.form.get('Last_name')
        phone_number = request.form.get('Number')
        email = request.form.get('Email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check DB connection
        if not db:
            flash("System Error: Database connection failed.", 'error')
            return render_template('signup.html')

        # Validate passwords
        if password != confirm_password:
            flash("Passwords do not match!", 'error')
            return render_template('signup.html')

        # Check if user exists
        if db.collection(USERS_COLLECTION).document(email).get().exists:
            flash("Email already registered. Please log in.", 'error')
            return render_template('signup.html')

        # Hash password securely
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Store data in Firestore
        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': phone_number,
            'email': email,
            'password': hashed_password,
        }
        db.collection(USERS_COLLECTION).document(email).set(user_data)

        flash("Registration successful! Please log in.", 'success')
        return redirect(url_for('handle_login'))

    return render_template('signup.html')


# --- 7. LOGOUT ROUTE ---
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", 'success')
    return redirect(url_for('index'))


# --- 8. RUN APP ---
if __name__ == '__main__':
    app.run(debug=True)
