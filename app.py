import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from functools import wraps

# --- Firebase and Database Imports (The Fix is here) ---
import firebase_admin 
from firebase_admin import credentials, initialize_app, firestore

# --- 1. CONFIGURATION AND INITIALIZATION ---
FIREBASE_CONFIG = os.environ.get('__firebase_config', '{}')
APP_ID = os.environ.get('__app_id', 'default-app-id')

app = Flask(__name__)

# CRITICAL: Secret key needed for sessions (cookies) and flash messages
app.secret_key = 'YOUR_SECURE_RANDOM_KEY_987654123' 

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Initialize Firebase Admin SDK and Firestore Client (ROBUST SETUP)
try:
    if not firebase_admin._apps:
        # initialize_app() looks for credentials automatically
        initialize_app()
    db = firestore.client()
except Exception as e:
    # This ensures the app doesn't crash if Firebase credentials are not found
    print(f"ERROR: Firebase/Firestore initialization failed. Authentication will be non-functional: {e}")
    db = None 

# Define the secure path for the user collection
USERS_COLLECTION = "users"

# --- 2. AUTHENTICATION DECORATOR ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("You must be logged in to view that page.", 'warning')
            return redirect(url_for('handle_login'))
        return f(*args, **kwargs)
    return decorated_function


# --- 3. STANDARD ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Protected routes
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
    # Placeholder to resolve the url_for('search_results') error in base.html
    return redirect(url_for('index'))

# --- 4. AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def handle_login():
    if request.method == 'POST':
        # Always use lowercase field names to match your HTML form
        email = request.form.get('email')
        password = request.form.get('password')

        # Safety check: make sure database is connected
        if not db:
            flash("System Error: Database connection failed.", 'error')
            return render_template('login.html')

        # 1️⃣ Try to find user document by email (works even if using .add())
        user_doc = db.collection(USERS_COLLECTION).document(email).get()
        user_data = None

        if not user_doc.exists:
            # Fallback: user documents might not use email as ID
            users_ref = db.collection(USERS_COLLECTION)
            query = users_ref.where("email", "==", email).limit(1).stream()
            for doc in query:
                user_data = doc.to_dict()
                break
        else:
            user_data = user_doc.to_dict()

        # 2️⃣ If user not found, show error
        if not user_data:
            flash("Invalid password or Email.", 'error')
            return render_template('login.html')

        # 3️⃣ Verify password
        stored_hash = user_data.get('password')
        if stored_hash and bcrypt.check_password_hash(stored_hash, password):
            # ✅ Success: set session & redirect
            session['logged_in'] = True
            session['user_email'] = email
            session['user_name'] = user_data.get('first_name', 'User')
            flash(f"Welcome back, {session['user_name']}!", 'success')
            return redirect(url_for('index'))
        else:
            # ❌ Wrong password
            flash("Invalid password or Email.", 'error')
            return render_template('login.html')

    # For GET requests
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def handle_signup():
    if request.method == 'POST':
        
        # 1. Capture all form data
        first_name = request.form.get('First_name')
        last_name = request.form.get('Last_name')
        phone_number = request.form.get('Number')
        email = request.form.get('Email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if DB is functional
        if not db:
            flash("System Error: Database connection failed.", 'error')
            return render_template('signup.html')
        
        # 2. Validation
        if password != confirm_password:
            flash("Passwords do not match!", 'error')
            return render_template('signup.html')

        # 3. Check if user exists
        if db.collection(USERS_COLLECTION).document(email).get().exists:
            flash("Email already registered. Please log in.", 'error')
            return render_template('signup.html')

        # 4. Securely Hash the Password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # 5. Save ALL Data to Firestore
        user_data = {
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': phone_number,
            'email': email,
            'password': hashed_password, # Stored Hash
        }
        db.collection(USERS_COLLECTION).document(email).set(user_data)
        
        # 6. Success and Redirect
        flash("Registration successful! Please log in.", 'success')
        return redirect(url_for('handle_login'))

    # If GET request, show the form
    return render_template('signup.html')

@app.route('/logout')
def logout():
    # Clear session data
    session.pop('logged_in', None)
    session.pop('user_email', None)
    session.pop('user_name', None)
    flash("You have been logged out.", 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)