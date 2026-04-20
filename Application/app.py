
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from datetime import datetime, time
from ultralytics import YOLO
from werkzeug.utils import secure_filename
from bson import ObjectId
import os
import secrets
import requests
from authlib.integrations.flask_client import OAuth
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
from rag_engine.generator import generate_ai_output
# ============================================================
# Flask App Setup
# ============================================================
app = Flask(__name__)
app.secret_key = "super_secret_key_Change_in_production_12345"
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg"}

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ============================================================
# Notification Scheduler Setup
# ============================================================
scheduler = BackgroundScheduler()
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# ============================================================
# OAuth Configuration - Manual Setup
# ============================================================
# GOOGLE_CLIENT_ID = "385671104468-hsv7huv7i87fan11jtui5hbvie7qlfed.apps.googleusercontent.com"
# GOOGLE_CLIENT_SECRET = "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"
# GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Manual Google OAuth configuration
GOOGLE_CONFIG = {
    "issuer": "https://accounts.google.com",
    "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
    
    "token_endpoint": "https://oauth2.googleapis.com/token",
    "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
    "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs"
}

oauth = OAuth(app)

try:
    google = oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=GOOGLE_DISCOVERY_URL,
        client_kwargs={
            'scope': 'openid email profile',
            'timeout': 30  # Add timeout
        }
    )
except Exception as e:
    print(f"Warning: Could not fetch OAuth metadata: {e}")
    # Fallback to manual configuration
    google = oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        api_base_url='https://www.googleapis.com/',
        access_token_url='https://oauth2.googleapis.com/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

# ============================================================
# MongoDB Setup
# ============================================================
client = MongoClient("mongodb://localhost:27017/")
db = client["dental_db"]
users_col = db["users"]
tracking_col = db["disease_tracking"]

# ============================================================
# YOLO Model
# ============================================================
model = YOLO("best.pt")

# ============================================================
# Recommendations
# ============================================================
recommendations = {
    "calculus": [
        {"time": "7:00 AM", "tip": "Brush thoroughly with tartar-control toothpaste to prevent buildup."},
        {"time": "8:00 AM", "tip": "Rinse your mouth with water after breakfast to clear food residues."},
        {"time": "12:30 PM", "tip": "Chew sugar-free gum after lunch to neutralize acids and prevent plaque."},
        {"time": "3:00 PM", "tip": "Drink water or rinse to keep your mouth clean during the day."},
        {"time": "7:00 PM", "tip": "Floss gently to remove plaque before it hardens into tartar."},
        {"time": "9:00 PM", "tip": "Use antiseptic mouthwash before sleep to eliminate bacteria."}
    ],

    "caries": [
        {"time": "7:00 AM", "tip": "Brush with fluoride toothpaste to strengthen enamel and fight cavities."},
        {"time": "8:00 AM", "tip": "Avoid sugary foods or drinks after breakfast to prevent decay."},
        {"time": "12:30 PM", "tip": "Rinse with water after lunch to wash away food particles."},
        {"time": "3:00 PM", "tip": "Snack on fruits or nuts instead of sweets for a healthy mouth."},
        {"time": "7:00 PM", "tip": "Floss after dinner to remove trapped food and reduce decay risk."},
        {"time": "9:00 PM", "tip": "Brush again before bed—never sleep without cleaning your teeth."}
    ],

    "gingivitis": [
        {"time": "7:00 AM", "tip": "Brush gently with a soft-bristle toothbrush using circular motions."},
        {"time": "8:00 AM", "tip": "Rinse with warm salt water to reduce gum inflammation."},
        {"time": "12:30 PM", "tip": "After lunch, massage your gums gently with clean fingers."},
        {"time": "3:00 PM", "tip": "Drink plenty of water to maintain gum moisture and flush bacteria."},
        {"time": "7:00 PM", "tip": "Floss gently and avoid hurting your gums."},
        {"time": "9:00 PM", "tip": "Use an antibacterial mouthwash to prevent bleeding gums overnight."}
    ],

    "mouth ulcer": [
        {"time": "7:00 AM", "tip": "Use SLS-free toothpaste to avoid irritating ulcers."},
        {"time": "8:00 AM", "tip": "Eat soft, cool foods for breakfast to prevent pain."},
        {"time": "12:30 PM", "tip": "Rinse with baking soda water after lunch to soothe ulcers."},
        {"time": "3:00 PM", "tip": "Drink cold water or aloe vera juice to reduce irritation."},
        {"time": "7:00 PM", "tip": "Avoid spicy or acidic foods during dinner."},
        {"time": "9:00 PM", "tip": "Apply ulcer gel before bed for faster healing."}
    ],

    "tooth discoloration": [
        {"time": "7:00 AM", "tip": "Brush with whitening toothpaste (limit to twice daily)."},
        {"time": "8:00 AM", "tip": "Rinse after coffee or tea to prevent stains."},
        {"time": "12:30 PM", "tip": "Eat crunchy fruits like apples to naturally clean enamel."},
        {"time": "3:00 PM", "tip": "Drink water instead of soda or colored beverages."},
        {"time": "7:00 PM", "tip": "Brush gently to remove surface stains after dinner."},
        {"time": "9:00 PM", "tip": "Use whitening mouthwash before bed to maintain brightness."}
    ],

    "hypodontia": [
        {"time": "7:00 AM", "tip": "Brush carefully around gaps to remove trapped food and plaque."},
        {"time": "8:00 AM", "tip": "Rinse with fluoride mouthwash after breakfast."},
        {"time": "12:30 PM", "tip": "Avoid biting hard foods during lunch to protect nearby teeth."},
        {"time": "3:00 PM", "tip": "Clean your aligner or denture (if used) and rinse your mouth."},
        {"time": "7:00 PM", "tip": "Floss gently, especially around dental gaps or bridges."},
        {"time": "9:00 PM", "tip": "Wear your night guard or retainer before sleeping."}
    ]
}


# ============================================================
# Flask-Login User Model
# ============================================================
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.email = user_data["email"]
        self.name = user_data["name"]
        self.auth_method = user_data.get("auth_method", "email")

@login_manager.user_loader
def load_user(user_id):
    user = users_col.find_one({"_id": ObjectId(user_id)})
    return User(user) if user else None

# ============================================================
# Helper Functions
# ============================================================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

def compare_areas(user_name):
    records = list(tracking_col.find({"patient_name": user_name}).sort("date", -1))
    if not records:
        return {"No Records": "Upload more scans to track changes."}

    class_progress = {}
    class_areas = {}

    for record in records:
        for det in record["detections"]:
            cls = det["class"]
            area = det.get("area", 0)
            class_areas.setdefault(cls, []).append(area)

    for cls, areas in class_areas.items():
        if len(areas) < 2:
            class_progress[cls] = "⚪ Not enough scans for comparison"
            continue

        latest_area = areas[0]
        previous_area = areas[1]
        diff = previous_area - latest_area

        if diff > 1000:
            class_progress[cls] = "🟢 Improved"
        elif diff < -1000:
            class_progress[cls] = "🔴 Worsened"
        else:
            class_progress[cls] = "⚪ No Significant Change"

    return class_progress

def create_or_get_google_user(user_info):
    """Find existing user or create new one for Google OAuth"""
    email = user_info['email']
    
    # Check if user exists
    user = users_col.find_one({"email": email})
    
    if user:
        # Update last login time
        users_col.update_one(
            {"_id": user["_id"]}, 
            {"$set": {"last_login": datetime.now()}}
        )
        return User(user)
    else:
        # Create new user
        user_data = {
            "name": user_info['name'],
            "email": email,
            "auth_method": "google",
            "registered_at": datetime.now(),
            "last_login": datetime.now(),
            "email_verified": True
        }
        
        result = users_col.insert_one(user_data)
        return User(users_col.find_one({"_id": result.inserted_id}))

def get_google_provider_cfg():
    """Get Google's OAuth provider configuration with error handling"""
    try:
        response = requests.get(GOOGLE_DISCOVERY_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Google discovery document: {e}")
        # Return manual configuration as fallback
        return GOOGLE_CONFIG

# ============================================================
# Notification Functions
# ============================================================

def get_user_notifications(user_email, user_name):
    """Get today's notifications for a specific user based on their dental conditions"""
    try:
        # Get user's latest dental scan results
        latest_scan = tracking_col.find_one(
            {"patient_name": user_name},
            sort=[("date", -1)]
        )
        
        if not latest_scan or not latest_scan.get("detections"):
            return []
        
        # Get detected conditions
        detected_conditions = [det["class"].lower() for det in latest_scan["detections"]]
        
        # Get current time
        now = datetime.now()
        current_time = now.strftime("%-I:%M %p")  # Format like "7:00 AM"
        
        # Find recommendations for current time
        today_notifications = []
        
        for condition in detected_conditions:
            if condition in recommendations:
                for rec in recommendations[condition]:
                    if rec["time"] == current_time:
                        today_notifications.append({
                            "condition": condition,
                            "time": rec["time"],
                            "tip": rec["tip"],
                            "user_email": user_email,
                            "user_name": user_name
                        })
        
        return today_notifications
    
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return []

def send_daily_notifications():
    """Send notifications to all users with dental conditions"""
    try:
        # Get all users
        all_users = users_col.find({})
        
        for user in all_users:
            notifications = get_user_notifications(user["email"], user["name"])
            
            for notification in notifications:
                # Here you can implement different notification methods:
                
                # 1. Store in database for in-app notifications
                store_notification_in_db(notification)
                
                # 2. Print to console (for development)
                print(f"NOTIFICATION for {notification['user_name']} at {notification['time']}:")
                print(f"  Condition: {notification['condition']}")
                print(f"  Tip: {notification['tip']}")
                print("-" * 50)
                
                # 3. Future: Email notifications
                # send_email_notification(notification)
                
                # 4. Future: Push notifications
                # send_push_notification(notification)
    
    except Exception as e:
        print(f"Error in daily notifications: {e}")

def store_notification_in_db(notification):
    """Store notification in database for in-app display"""
    try:
        db["notifications"].insert_one({
            "user_email": notification["user_email"],
            "user_name": notification["user_name"],
            "condition": notification["condition"],
            "time": notification["time"],
            "tip": notification["tip"],
            "timestamp": datetime.now(),
            "read": False
        })
    except Exception as e:
        print(f"Error storing notification: {e}")

# ============================================================
# Schedule Notifications
# ============================================================

def schedule_notifications():
    """Schedule notifications for different times of the day"""
    
    # Schedule for different times (you can add more times as needed)
    notification_times = [
        {"hour": 7, "minute": 0},   # 7:00 AM
        {"hour": 8, "minute": 0},   # 8:00 AM  
        {"hour": 12, "minute": 30}, # 12:30 PM
        {"hour": 15, "minute": 0},  # 3:00 PM
        {"hour": 19, "minute": 0},  # 7:00 PM
        {"hour": 21, "minute": 0},  # 9:00 PM
    ]
    
    for time_slot in notification_times:
        scheduler.add_job(
            func=send_daily_notifications,
            trigger=CronTrigger(
                hour=time_slot["hour"],
                minute=time_slot["minute"],
                timezone="UTC"  # Adjust to your timezone
            ),
            id=f"notification_{time_slot['hour']}_{time_slot['minute']}",
            replace_existing=True
        )
    
    print("Scheduled notifications for:", [f"{t['hour']}:{t['minute']}" for t in notification_times])

# ============================================================
# Routes
# ============================================================
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("index.html")



@app.route("/dashboard")
@login_required
def index():
    return render_template("index.html", user=current_user)

# Google OAuth Routes - Manual Implementation
@app.route("/google-login")
def google_login():
    try:
        # Generate state parameter for security
        session['oauth_state'] = secrets.token_urlsafe(16)
        
        # Get Google provider configuration
        google_provider_cfg = get_google_provider_cfg()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        # Create the authorization request URL
        redirect_uri = url_for('google_callback', _external=True)
        
        request_url = (
            f"{authorization_endpoint}"
            f"?client_id={GOOGLE_CLIENT_ID}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
            f"&redirect_uri={redirect_uri}"
            f"&state={session['oauth_state']}"
            f"&access_type=offline"
        )
        
        return redirect(request_url)
        
    except Exception as e:
        flash(f"OAuth configuration error: {str(e)}", "danger")
        return redirect(url_for('login'))

@app.route("/authorize")
def google_callback():
    # Verify state parameter
    if session.get('oauth_state') != request.args.get('state'):
        flash("Invalid state parameter - possible CSRF attack", "danger")
        return redirect(url_for('login'))
    
    # Check for error
    if 'error' in request.args:
        flash(f"Authorization failed: {request.args.get('error')}", "danger")
        return redirect(url_for('login'))
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        flash("No authorization code received", "danger")
        return redirect(url_for('login'))
    
    try:
        # Get Google provider configuration
        google_provider_cfg = get_google_provider_cfg()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        # Prepare token request
        redirect_uri = url_for('google_callback', _external=True)
        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        token_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Exchange code for token
        token_response = requests.post(
            token_endpoint,
            data=token_data,
            headers=token_headers,
            timeout=30
        )
        token_response.raise_for_status()
        tokens = token_response.json()
        
        # Get user info
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        userinfo_headers = {
            'Authorization': f"Bearer {tokens['access_token']}"
        }
        
        userinfo_response = requests.get(
            userinfo_endpoint,
            headers=userinfo_headers,
            timeout=30
        )
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()
        
        # Create or get user
        user = create_or_get_google_user(user_info)
        login_user(user)
        flash(f"Welcome {user.name}! 👋", "success")
        return redirect(url_for('index'))
        
    except requests.exceptions.RequestException as e:
        flash(f"Authentication failed: {str(e)}", "danger")
        return redirect(url_for('login'))
    except Exception as e:
        flash(f"Unexpected error: {str(e)}", "danger")
        return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if users_col.find_one({"email": email}):
            flash("Email already exists", "warning")
            return redirect(url_for("register"))

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        result = users_col.insert_one({
            "name": name,
            "email": email,
            "password": hashed_pw,
            "auth_method": "email",
            "registered_at": datetime.now(),
            "last_login": datetime.now()
        })

        user_obj = User(users_col.find_one({"_id": result.inserted_id}))
        login_user(user_obj)
        flash("Registration successful! Welcome 👋", "success")
        return redirect(url_for("index"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users_col.find_one({"email": email})
        if user and user.get("auth_method") == "google":
            flash("This account was created with Google. Please use Google to sign in.", "warning")
            return redirect(url_for('login'))
            
        if user and bcrypt.check_password_hash(user["password"], password):
            login_user(User(user))
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("home"))

@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    if "file" not in request.files:
        flash("No file uploaded", "danger")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        flash("Invalid file type", "warning")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # 🔍 Run YOLO prediction
    results = model.predict(filepath, save=False)
    detections = []

    # 💾 Save output image
    output_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename.rsplit(".", 1)[0] + "_pred.jpg"
    )
    results[0].save(filename=output_path)

    # 📊 Extract detection data
    for box in results[0].boxes:
        cls_id = int(box.cls)
        cls_name = model.names[cls_id]

        x1, y1, x2, y2 = map(float, box.xyxy[0])
        area = (x2 - x1) * (y2 - y1)

        detections.append({
            "class": cls_name,
            "area": round(area, 2)
        })

    # 🗄 Store scan in MongoDB
    tracking_col.insert_one({
        "patient_name": current_user.name,
        "image": output_path,
        "detections": detections,
        "date": datetime.now()
    })

    # 🧠 Extract condition names
    conditions = [d["class"].lower() for d in detections]

    # 👤 Get user lifestyle data
    user = users_col.find_one({"_id": ObjectId(current_user.id)})
    lifestyle = user.get("lifestyle", {})

    # 🤖 Generate AI recommendations using RAG
    result = generate_ai_output(conditions, lifestyle)

    # 💾 Store AI report in user document
    users_col.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"ai_report": result}}
    )

    # 🔔 (Optional) keep notifications
    schedule_notifications()

    # 🚀 Redirect to recommendations page
    return redirect(url_for("rec_page"))

@app.route("/progress")
@login_required
def progress():
    records = list(tracking_col.find({"patient_name": current_user.name}).sort("date", -1))
    if not records:
        flash("No scans found yet. Upload an image to start tracking!", "info")
        return render_template("progress.html", user=current_user, tracking_summary=None, records=[])
    
    tracking_summary = compare_areas(current_user.name)
    return render_template("progress.html", user=current_user, tracking_summary=tracking_summary, records=records)

# @app.route("/recommendations")
# @login_required
# def rec_page():
#     return render_template("recommendations.html", user=current_user, recommendations=recommendations)

# ===========================
# LIFESTYLE ROUTES

# ===========================

@app.route('/lifestyle')
@login_required
def lifestyle():
    user = users_col.find_one({"_id": ObjectId(current_user.id)})
    lifestyle_data = user.get("lifestyle", None)

    return render_template(
        'lifestyle.html',
        lifestyle=lifestyle_data,
        user=current_user
    )


@app.route("/save_lifestyle", methods=["POST"])
@login_required
def save_lifestyle():
    try:
        lifestyle_data = {
            "age": request.form.get("age"),
            "person": request.form.get("person"),
            "brush": request.form.get("brush"),
            "food": request.form.getlist("food"),
            "tobacco": request.form.get("tobacco"),
            "issues": request.form.getlist("issues"),
            "diabetes": request.form.get("diabetes"),
            "visit": request.form.get("visit"),
            "updated_at": datetime.now()
        }

        users_col.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": {"lifestyle": lifestyle_data}}
        )

        flash("Thanks! Your lifestyle data helps us give better dental insights 🦷", "success")
        return redirect(url_for("lifestyle"))

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for("lifestyle"))
    

# ============================================================
# New Routes for Notifications
# ============================================================

@app.route("/notifications")
@login_required
def user_notifications():
    """Display user's notifications"""
    user_notifs = list(db["notifications"].find(
        {"user_email": current_user.email},
        sort=[("timestamp", -1)]
    ))
    
    # Mark as read when user views them
    db["notifications"].update_many(
        {"user_email": current_user.email, "read": False},
        {"$set": {"read": True}}
    )
    
    return render_template("notifications.html", 
                         user=current_user, 
                         notifications=user_notifs)

@app.route("/notifications/clear", methods=["POST"])
@login_required
def clear_notifications():
    """Clear all read notifications"""
    db["notifications"].delete_many({
        "user_email": current_user.email,
        "read": True
    })
    flash("Notifications cleared", "success")
    return redirect(url_for("user_notifications"))

# ============================================================
# Context Processor for Unread Notifications Count
# ============================================================
@app.context_processor
def inject_db():
    return dict(db=db)

@app.context_processor
def inject_unread_count():
    if current_user.is_authenticated:
        unread_count = db["notifications"].count_documents({
            "user_email": current_user.email,
            "read": False
        })
        return dict(unread_count=unread_count)
    return dict(unread_count=0)

# ============================================================
# Initialize scheduler when app starts (FIXED)
# ============================================================

# Use the modern way to initialize on first request
scheduler_initialized = False

@app.before_request
def initialize_scheduler_on_first_request():
    global scheduler_initialized
    if not scheduler_initialized:
        schedule_notifications()
        scheduler_initialized = True
        print("Scheduler initialized successfully!")




@app.route("/generate_report")
@login_required
def generate_report():

    user = users_col.find_one({"_id": ObjectId(current_user.id)})

    # 🔍 Get latest detection
    latest = tracking_col.find_one(
        {"patient_name": current_user.name},
        sort=[("date", -1)]
    )

    conditions = []
    if latest:
        conditions = [d["class"].lower() for d in latest["detections"]]

    # 🧠 Get lifestyle
    lifestyle = user.get("lifestyle", {})

    # 🤖 Generate using RAG
    result = generate_ai_output(conditions, lifestyle)

    # 💾 Store in DB
    users_col.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"ai_report": result}}
    )

    return redirect(url_for("rec_page"))



@app.route("/recommendations")
@login_required
def rec_page():
    user = users_col.find_one({"_id": ObjectId(current_user.id)})

    report = user.get("ai_report")

    latest = tracking_col.find_one(
        {"patient_name": current_user.name},
        sort=[("date", -1)]
    )

    conditions = []
    if latest:
        conditions = [d["class"] for d in latest["detections"]]

    return render_template(
        "recommendations.html",
        report=report,
        conditions=conditions
    )


# ============================================================
# Run App
# ============================================================
if __name__ == "__main__":
    os.makedirs("static/uploads", exist_ok=True)
    
    # Initialize MongoDB collections
    if "notifications" not in db.list_collection_names():
        print("Created notifications collection")
    
    app.run(debug=True, host='0.0.0.0', port=5000)












































































# from flask import Flask, render_template, request, redirect, url_for, flash, session
# from flask_bcrypt import Bcrypt
# from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# from pymongo import MongoClient
# from datetime import datetime, time
# from ultralytics import YOLO
# from werkzeug.utils import secure_filename
# from bson import ObjectId
# import os
# import secrets
# import requests
# from authlib.integrations.flask_client import OAuth
# import json
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.cron import CronTrigger
# import atexit

# # ============================================================
# # Flask App Setup
# # ============================================================
# app = Flask(__name__)
# app.secret_key = "super_secret_key_Change_in_production_12345"
# app.config["UPLOAD_FOLDER"] = "static/uploads"
# app.config["ALLOWED_EXTENSIONS"] = {"png", "jpg", "jpeg"}

# bcrypt = Bcrypt(app)
# login_manager = LoginManager(app)
# login_manager.login_view = "login"

# # ============================================================
# # Notification Scheduler Setup
# # ============================================================
# scheduler = BackgroundScheduler()
# scheduler.start()

# # Shut down the scheduler when exiting the app
# atexit.register(lambda: scheduler.shutdown())

# # ============================================================
# # OAuth Configuration - Manual Setup
# # ============================================================
# GOOGLE_CLIENT_ID = "385671104468-hsv7huv7i87fan11jtui5hbvie7qlfed.apps.googleusercontent.com"
# GOOGLE_CLIENT_SECRET = "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"
# GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# # Manual Google OAuth configuration
# GOOGLE_CONFIG = {
#     "issuer": "https://accounts.google.com",
#     "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
#     "token_endpoint": "https://oauth2.googleapis.com/token",
#     "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
#     "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs"
# }

# oauth = OAuth(app)

# try:
#     google = oauth.register(
#         name='google',
#         client_id=GOOGLE_CLIENT_ID,
#         client_secret=GOOGLE_CLIENT_SECRET,
#         server_metadata_url=GOOGLE_DISCOVERY_URL,
#         client_kwargs={
#             'scope': 'openid email profile',
#             'timeout': 30  # Add timeout
#         }
#     )
# except Exception as e:
#     print(f"Warning: Could not fetch OAuth metadata: {e}")
#     # Fallback to manual configuration
#     google = oauth.register(
#         name='google',
#         client_id=GOOGLE_CLIENT_ID,
#         client_secret=GOOGLE_CLIENT_SECRET,
#         api_base_url='https://www.googleapis.com/',
#         access_token_url='https://oauth2.googleapis.com/token',
#         authorize_url='https://accounts.google.com/o/oauth2/auth',
#         client_kwargs={
#             'scope': 'openid email profile'
#         }
#     )

# # ============================================================
# # MongoDB Setup
# # ============================================================
# client = MongoClient("mongodb://localhost:27017/")
# db = client["dental_db"]
# users_col = db["users"]
# tracking_col = db["disease_tracking"]

# # ============================================================
# # Initialize MongoDB Collections
# # ============================================================
# def initialize_database():
#     """Initialize all required MongoDB collections"""
#     try:
#         # Create collections if they don't exist by inserting a dummy document
#         collections_to_create = ["users", "disease_tracking", "notifications"]
        
#         for collection_name in collections_to_create:
#             if collection_name not in db.list_collection_names():
#                 # Create collection by inserting and immediately deleting a document
#                 db[collection_name].insert_one({"initialized": True, "timestamp": datetime.now()})
#                 db[collection_name].delete_one({"initialized": True})
#                 print(f"✅ Created collection: {collection_name}")
#             else:
#                 print(f"✅ Collection already exists: {collection_name}")
                
#         # Create indexes for better performance
#         db.users.create_index("email", unique=True)
#         db.disease_tracking.create_index([("patient_name", 1), ("date", -1)])
#         db.notifications.create_index([("user_email", 1), ("timestamp", -1)])
#         db.notifications.create_index([("user_email", 1), ("read", 1)])
        
#         print("✅ Database initialization completed successfully!")
        
#     except Exception as e:
#         print(f"❌ Database initialization error: {e}")

# # ============================================================
# # YOLO Model
# # ============================================================
# model = YOLO("best.pt")

# # ============================================================
# # Recommendations
# # ============================================================
# recommendations = {
#     "calculus": [
#         {"time": "7:00 AM", "tip": "Brush with tartar-control toothpaste"},
#         {"time": "8:00 AM", "tip": "Rinse mouth with water after breakfast"},
#         {"time": "12:30 PM", "tip": "Chew sugar-free gum to reduce plaque"},
#         {"time": "7:00 PM", "tip": "Floss before plaque hardens into tartar"},
#         {"time": "9:00 PM", "tip": "Use antiseptic mouthwash"},
#         {"time": "Weekly", "tip": "Professional scaling every 6 months"}
#     ],
#     "caries": [
#         {"time": "7:00 AM", "tip": "Brush with fluoride toothpaste"},
#         {"time": "3:00 PM", "tip": "Avoid sugary snacks"},
#         {"time": "7:00 PM", "tip": "Floss after dinner"},
#         {"time": "Bedtime", "tip": "Never sleep without brushing"},
#         {"time": "Weekly", "tip": "Visit dentist for early treatment"}
#     ],
#     "gingivitis": [
#         {"time": "7:00 AM", "tip": "Brush gently with soft-bristle brush"},
#         {"time": "1:00 PM", "tip": "Rinse with warm salt water"},
#         {"time": "7:00 PM", "tip": "Massage gums gently"},
#         {"time": "Monthly", "tip": "Get gum health checkup"}
#     ],
#     "mouth ulcer": [
#         {"time": "7:00 AM", "tip": "Avoid toothpaste with SLS"},
#         {"time": "Breakfast", "tip": "Eat soft, cool foods"},
#         {"time": "After meals", "tip": "Rinse with baking soda water"},
#         {"time": "Bedtime", "tip": "Apply ulcer gel"}
#     ],
#     "tooth discoloration": [
#         {"time": "7:00 AM", "tip": "Use whitening toothpaste (max 2x/day)"},
#         {"time": "After coffee", "tip": "Rinse immediately"},
#         {"time": "Weekly", "tip": "Try oil pulling for 10 mins"},
#         {"time": "Quarterly", "tip": "Professional cleaning recommended"}
#     ],
#     "hypodontia": [
#         {"time": "7:00 AM", "tip": "Brush carefully around gaps"},
#         {"time": "Lunch", "tip": "Avoid hard foods"},
#         {"time": "9:00 PM", "tip": "Wear night guard if needed"},
#         {"time": "Annually", "tip": "Consult orthodontist for implants"}
#     ]
# }

# # ============================================================
# # Flask-Login User Model
# # ============================================================
# class User(UserMixin):
#     def __init__(self, user_data):
#         self.id = str(user_data["_id"])
#         self.email = user_data["email"]
#         self.name = user_data["name"]
#         self.auth_method = user_data.get("auth_method", "email")

# @login_manager.user_loader
# def load_user(user_id):
#     user = users_col.find_one({"_id": ObjectId(user_id)})
#     return User(user) if user else None

# # ============================================================
# # Helper Functions
# # ============================================================
# def allowed_file(filename):
#     return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

# def compare_areas(user_name):
#     records = list(tracking_col.find({"patient_name": user_name}).sort("date", -1))
#     if not records:
#         return {"No Records": "Upload more scans to track changes."}

#     class_progress = {}
#     class_areas = {}

#     for record in records:
#         for det in record["detections"]:
#             cls = det["class"]
#             area = det.get("area", 0)
#             class_areas.setdefault(cls, []).append(area)

#     for cls, areas in class_areas.items():
#         if len(areas) < 2:
#             class_progress[cls] = "⚪ Not enough scans for comparison"
#             continue

#         latest_area = areas[0]
#         previous_area = areas[1]
#         diff = previous_area - latest_area

#         if diff < -1000:
#             class_progress[cls] = "🟢 Improved"
#         elif diff > 1000:
#             class_progress[cls] = "🔴 Worsened"
#         else:
#             class_progress[cls] = "⚪ No Significant Change"

#     return class_progress

# def create_or_get_google_user(user_info):
#     """Find existing user or create new one for Google OAuth"""
#     email = user_info['email']
    
#     # Check if user exists
#     user = users_col.find_one({"email": email})
    
#     if user:
#         # Update last login time
#         users_col.update_one(
#             {"_id": user["_id"]}, 
#             {"$set": {"last_login": datetime.now()}}
#         )
#         return User(user)
#     else:
#         # Create new user
#         user_data = {
#             "name": user_info['name'],
#             "email": email,
#             "auth_method": "google",
#             "registered_at": datetime.now(),
#             "last_login": datetime.now(),
#             "email_verified": True
#         }
        
#         result = users_col.insert_one(user_data)
#         return User(users_col.find_one({"_id": result.inserted_id}))

# def get_google_provider_cfg():
#     """Get Google's OAuth provider configuration with error handling"""
#     try:
#         response = requests.get(GOOGLE_DISCOVERY_URL, timeout=10)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching Google discovery document: {e}")
#         # Return manual configuration as fallback
#         return GOOGLE_CONFIG

# # ============================================================
# # Notification Functions
# # ============================================================

# def get_user_notifications(user_email, user_name):
#     """Get today's notifications for a specific user based on their dental conditions"""
#     try:
#         # Get user's latest dental scan results
#         latest_scan = tracking_col.find_one(
#             {"patient_name": user_name},
#             sort=[("date", -1)]
#         )
        
#         if not latest_scan or not latest_scan.get("detections"):
#             return []
        
#         # Get detected conditions
#         detected_conditions = [det["class"].lower() for det in latest_scan["detections"]]
        
#         # Get current time
#         now = datetime.now()
#         current_time = now.strftime("%-I:%M %p")  # Format like "7:00 AM"
        
#         # Find recommendations for current time
#         today_notifications = []
        
#         for condition in detected_conditions:
#             if condition in recommendations:
#                 for rec in recommendations[condition]:
#                     if rec["time"] == current_time:
#                         today_notifications.append({
#                             "condition": condition,
#                             "time": rec["time"],
#                             "tip": rec["tip"],
#                             "user_email": user_email,
#                             "user_name": user_name
#                         })
        
#         return today_notifications
    
#     except Exception as e:
#         print(f"Error getting notifications: {e}")
#         return []

# def send_daily_notifications():
#     """Send notifications to all users with dental conditions"""
#     try:
#         print(f"Running daily notifications check at {datetime.now()}")
        
#         # Get all users
#         all_users = list(users_col.find({}))
#         print(f"Found {len(all_users)} users to check for notifications")
        
#         total_notifications = 0
        
#         for user in all_users:
#             notifications = get_user_notifications(user["email"], user["name"])
            
#             for notification in notifications:
#                 # Store in database for in-app notifications
#                 store_notification_in_db(notification)
#                 total_notifications += 1
                
#                 # Print to console (for development)
#                 print(f"📨 NOTIFICATION for {notification['user_name']} at {notification['time']}:")
#                 print(f"   Condition: {notification['condition']}")
#                 print(f"   Tip: {notification['tip']}")
#                 print("-" * 50)
        
#         print(f"Sent {total_notifications} notifications to {len(all_users)} users")
    
#     except Exception as e:
#         print(f"Error in daily notifications: {e}")

# def store_notification_in_db(notification):
#     """Store notification in database for in-app display"""
#     try:
#         # Ensure notifications collection exists
#         if "notifications" not in db.list_collection_names():
#             initialize_database()
            
#         result = db["notifications"].insert_one({
#             "user_email": notification["user_email"],
#             "user_name": notification["user_name"],
#             "condition": notification["condition"],
#             "time": notification["time"],
#             "tip": notification["tip"],
#             "timestamp": datetime.now(),
#             "read": False
#         })
#         print(f"Stored notification in database with ID: {result.inserted_id}")
        
#     except Exception as e:
#         print(f"Error storing notification: {e}")

# # ============================================================
# # Schedule Notifications
# # ============================================================

# def schedule_notifications():
#     """Schedule notifications for different times of the day"""
    
#     # Clear existing jobs to avoid duplicates
#     scheduler.remove_all_jobs()
    
#     # Schedule for different times (you can add more times as needed)
#     notification_times = [
#         {"hour": 7, "minute": 0},   # 7:00 AM
#         {"hour": 8, "minute": 0},   # 8:00 AM  
#         {"hour": 12, "minute": 30}, # 12:30 PM
#         {"hour": 15, "minute": 0},  # 3:00 PM
#         {"hour": 19, "minute": 0},  # 7:00 PM
#         {"hour": 21, "minute": 0},  # 9:00 PM
#     ]
    
#     for time_slot in notification_times:
#         scheduler.add_job(
#             func=send_daily_notifications,
#             trigger=CronTrigger(
#                 hour=time_slot["hour"],
#                 minute=time_slot["minute"],
#                 timezone="UTC"  # Adjust to your timezone
#             ),
#             id=f"notification_{time_slot['hour']}_{time_slot['minute']}",
#             replace_existing=True
#         )
#         print(f"⏰ Scheduled notification job for {time_slot['hour']:02d}:{time_slot['minute']:02d}")
    
#     print("✅ All notification jobs scheduled successfully!")
#     print(f"📅 Total scheduled times: {len(notification_times)}")

# # ============================================================
# # Routes
# # ============================================================
# @app.route("/")
# def home():
#     if current_user.is_authenticated:
#         return redirect(url_for("index"))
#     return render_template("index.html")

# @app.route("/dashboard")
# @login_required
# def index():
#     return render_template("index.html", user=current_user)

# # Google OAuth Routes - Manual Implementation
# @app.route("/google-login")
# def google_login():
#     try:
#         # Generate state parameter for security
#         session['oauth_state'] = secrets.token_urlsafe(16)
        
#         # Get Google provider configuration
#         google_provider_cfg = get_google_provider_cfg()
#         authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
#         # Create the authorization request URL
#         redirect_uri = url_for('google_callback', _external=True)
        
#         request_url = (
#             f"{authorization_endpoint}"
#             f"?client_id={GOOGLE_CLIENT_ID}"
#             f"&response_type=code"
#             f"&scope=openid%20email%20profile"
#             f"&redirect_uri={redirect_uri}"
#             f"&state={session['oauth_state']}"
#             f"&access_type=offline"
#         )
        
#         return redirect(request_url)
        
#     except Exception as e:
#         flash(f"OAuth configuration error: {str(e)}", "danger")
#         return redirect(url_for('login'))

# @app.route("/authorize")
# def google_callback():
#     # Verify state parameter
#     if session.get('oauth_state') != request.args.get('state'):
#         flash("Invalid state parameter - possible CSRF attack", "danger")
#         return redirect(url_for('login'))
    
#     # Check for error
#     if 'error' in request.args:
#         flash(f"Authorization failed: {request.args.get('error')}", "danger")
#         return redirect(url_for('login'))
    
#     # Get authorization code
#     code = request.args.get('code')
#     if not code:
#         flash("No authorization code received", "danger")
#         return redirect(url_for('login'))
    
#     try:
#         # Get Google provider configuration
#         google_provider_cfg = get_google_provider_cfg()
#         token_endpoint = google_provider_cfg["token_endpoint"]
        
#         # Prepare token request
#         redirect_uri = url_for('google_callback', _external=True)
#         token_data = {
#             'client_id': GOOGLE_CLIENT_ID,
#             'client_secret': GOOGLE_CLIENT_SECRET,
#             'code': code,
#             'grant_type': 'authorization_code',
#             'redirect_uri': redirect_uri
#         }
        
#         token_headers = {
#             'Content-Type': 'application/x-www-form-urlencoded'
#         }
        
#         # Exchange code for token
#         token_response = requests.post(
#             token_endpoint,
#             data=token_data,
#             headers=token_headers,
#             timeout=30
#         )
#         token_response.raise_for_status()
#         tokens = token_response.json()
        
#         # Get user info
#         userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
#         userinfo_headers = {
#             'Authorization': f"Bearer {tokens['access_token']}"
#         }
        
#         userinfo_response = requests.get(
#             userinfo_endpoint,
#             headers=userinfo_headers,
#             timeout=30
#         )
#         userinfo_response.raise_for_status()
#         user_info = userinfo_response.json()
        
#         # Create or get user
#         user = create_or_get_google_user(user_info)
#         login_user(user)
#         flash(f"Welcome {user.name}! 👋", "success")
#         return redirect(url_for('index'))
        
#     except requests.exceptions.RequestException as e:
#         flash(f"Authentication failed: {str(e)}", "danger")
#         return redirect(url_for('login'))
#     except Exception as e:
#         flash(f"Unexpected error: {str(e)}", "danger")
#         return redirect(url_for('login'))

# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         name = request.form["name"]
#         email = request.form["email"]
#         password = request.form["password"]

#         if users_col.find_one({"email": email}):
#             flash("Email already exists", "warning")
#             return redirect(url_for("register"))

#         hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
#         result = users_col.insert_one({
#             "name": name,
#             "email": email,
#             "password": hashed_pw,
#             "auth_method": "email",
#             "registered_at": datetime.now(),
#             "last_login": datetime.now()
#         })

#         user_obj = User(users_col.find_one({"_id": result.inserted_id}))
#         login_user(user_obj)
#         flash("Registration successful! Welcome 👋", "success")
#         return redirect(url_for("index"))

#     return render_template("register.html")

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         email = request.form["email"]
#         password = request.form["password"]

#         user = users_col.find_one({"email": email})
#         if user and user.get("auth_method") == "google":
#             flash("This account was created with Google. Please use Google to sign in.", "warning")
#             return redirect(url_for('login'))
            
#         if user and bcrypt.check_password_hash(user["password"], password):
#             login_user(User(user))
#             flash("Login successful!", "success")
#             return redirect(url_for("index"))
#         else:
#             flash("Invalid credentials", "danger")

#     return render_template("login.html")

# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     session.clear()
#     flash("Logged out successfully.", "info")
#     return redirect(url_for("home"))

# @app.route("/analyze", methods=["POST"])
# @login_required
# def analyze():
#     if "file" not in request.files:
#         flash("No file uploaded", "danger")
#         return redirect(url_for("index"))

#     file = request.files["file"]
#     if file.filename == "" or not allowed_file(file.filename):
#         flash("Invalid file type", "warning")
#         return redirect(url_for("index"))

#     filename = secure_filename(file.filename)
#     filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
#     file.save(filepath)

#     # Run YOLO prediction
#     results = model.predict(filepath, save=False)
#     detections = []

#     # Save output image
#     output_path = os.path.join(
#         app.config["UPLOAD_FOLDER"], filename.rsplit(".", 1)[0] + "_pred.jpg"
#     )
#     results[0].save(filename=output_path)

#     # Extract detection data
#     for box in results[0].boxes:
#         cls_id = int(box.cls)
#         cls_name = model.names[cls_id]

#         # Calculate bounding box area
#         x1, y1, x2, y2 = map(float, box.xyxy[0])
#         area = (x2 - x1) * (y2 - y1)

#         detections.append({
#             "class": cls_name,
#             "area": round(area, 2),
#             "advice": recommendations.get(cls_name.lower(), [])
#         })

#     # Store in MongoDB
#     tracking_col.insert_one({
#         "patient_name": current_user.name,
#         "image": output_path,
#         "detections": detections,
#         "date": datetime.now()
#     })

#     tracking_summary = compare_areas(current_user.name)
    
#     # Schedule notifications for new conditions
#     schedule_notifications()

#     return render_template(
#         "result.html",
#         user_image=output_path,
#         detections=detections,
#         tracking_summary=tracking_summary,
#         user=current_user
#     )

# @app.route("/progress")
# @login_required
# def progress():
#     records = list(tracking_col.find({"patient_name": current_user.name}).sort("date", -1))
#     if not records:
#         flash("No scans found yet. Upload an image to start tracking!", "info")
#         return render_template("progress.html", user=current_user, tracking_summary=None, records=[])
    
#     tracking_summary = compare_areas(current_user.name)
#     return render_template("progress.html", user=current_user, tracking_summary=tracking_summary, records=records)

# @app.route("/recommendations")
# @login_required
# def rec_page():
#     return render_template("recommendations.html", user=current_user, recommendations=recommendations)

# # ============================================================
# # New Routes for Notifications
# # ============================================================

# @app.route("/notifications")
# @login_required
# def user_notifications():
#     """Display user's notifications"""
#     try:
#         # Ensure notifications collection exists
#         if "notifications" not in db.list_collection_names():
#             initialize_database()
            
#         user_notifs = list(db["notifications"].find(
#             {"user_email": current_user.email},
#             sort=[("timestamp", -1)]
#         ))
        
#         # Mark as read when user views them
#         db["notifications"].update_many(
#             {"user_email": current_user.email, "read": False},
#             {"$set": {"read": True}}
#         )
        
#         print(f"📋 Loaded {len(user_notifs)} notifications for {current_user.email}")
        
#         return render_template("notifications.html", 
#                              user=current_user, 
#                              notifications=user_notifs)
                             
#     except Exception as e:
#         print(f"❌ Error loading notifications: {e}")
#         flash("Error loading notifications", "danger")
#         return render_template("notifications.html", user=current_user, notifications=[])

# @app.route("/notifications/clear", methods=["POST"])
# @login_required
# def clear_notifications():
#     """Clear all read notifications"""
#     try:
#         result = db["notifications"].delete_many({
#             "user_email": current_user.email,
#             "read": True
#         })
#         flash(f"Cleared {result.deleted_count} read notifications", "success")
#         print(f"🗑️ Cleared {result.deleted_count} read notifications for {current_user.email}")
#     except Exception as e:
#         print(f"❌ Error clearing notifications: {e}")
#         flash("Error clearing notifications", "danger")
    
#     return redirect(url_for("user_notifications"))

# # ============================================================
# # Context Processor for Unread Notifications Count
# # ============================================================
# @app.context_processor
# def inject_unread_count():
#     if current_user.is_authenticated:
#         try:
#             # Ensure notifications collection exists
#             if "notifications" not in db.list_collection_names():
#                 initialize_database()
#                 return dict(unread_count=0)
                
#             unread_count = db["notifications"].count_documents({
#                 "user_email": current_user.email,
#                 "read": False
#             })
#             return dict(unread_count=unread_count)
#         except Exception as e:
#             print(f"❌ Error counting unread notifications: {e}")
#             return dict(unread_count=0)
#     return dict(unread_count=0)

# # ============================================================
# # Initialize scheduler when app starts (FIXED)
# # ============================================================

# # Use the modern way to initialize on first request
# scheduler_initialized = False

# @app.before_request
# def initialize_scheduler_on_first_request():
#     global scheduler_initialized
#     if not scheduler_initialized:
#         # Initialize database first
#         initialize_database()
#         # Then schedule notifications
#         schedule_notifications()
#         scheduler_initialized = True
#         print("🎉 Application initialized successfully!")

# # ============================================================
# # Run App
# # ============================================================
# if __name__ == "__main__":
#     os.makedirs("static/uploads", exist_ok=True)
    
#     # Initialize database on startup
#     initialize_database()
    
#     print("🚀 Starting DentalAI Flask Application...")
#     print("📍 Notification times: 7:00 AM, 8:00 AM, 12:30 PM, 3:00 PM, 7:00 PM, 9:00 PM")
#     print("📊 Database collections initialized")
#     print("⏰ Notification scheduler ready")
    
#     app.run(debug=True, host='0.0.0.0', port=5000)