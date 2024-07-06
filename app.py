from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from PIL import Image
import os
import uuid
import json
import logging

app = Flask(__name__)

instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'database.db')
print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])  # Debugging

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['WTF_CSRF_SECRET_KEY'] = 'supersecretkey'  # Can be the same as your SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-WTF CSRF protection
csrf = CSRFProtect(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class BusinessCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    job_title = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    logo = db.Column(db.String(100))
    profile_picture = db.Column(db.String(100))
    social_media = db.Column(db.JSON)
    products_services = db.Column(db.JSON)
    card_url = db.Column(db.String(100), unique=True, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(image_path, max_size=(300, 300)):
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        img.save(image_path)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    app.logger.info(f"Registration attempt for username: {data.get('username')}")
    
    if User.query.filter_by(username=data.get('username')).first():
        app.logger.warning(f"Registration failed: Username already exists: {data.get('username')}")
        return jsonify({"success": False, "message": "Username already exists"}), 400

    hashed_password = generate_password_hash(data.get('password'))
    new_user = User(username=data.get('username'), password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    app.logger.info(f"Registration successful for username: {new_user.username}")
    return jsonify({"success": True, "message": "Registration successful"})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    app.logger.info(f"Login attempt for username: {data.get('username')}")
    
    user = User.query.filter_by(username=data.get('username')).first()
    if user and check_password_hash(user.password, data.get('password')):
        login_user(user)
        app.logger.info(f"Login successful for user: {user.username}")
        return jsonify({"success": True, "message": "Login successful"})
    else:
        app.logger.warning(f"Login failed for username: {data.get('username')}")
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route('/api/create_card', methods=['POST'])
@login_required
def create_card():
    data = request.form.to_dict()
    app.logger.info(f"Form data received: {data}")

    # Handle file uploads
    logo = request.files.get('logo')
    profile_picture = request.files.get('profile_picture')

    if logo and allowed_file(logo.filename):
        logo_filename = secure_filename(logo.filename)
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
        logo.save(logo_path)
        data['logo'] = logo_filename
        resize_image(logo_path)

    if profile_picture and allowed_file(profile_picture.filename):
        profile_filename = secure_filename(profile_picture.filename)
        profile_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_filename)
        profile_picture.save(profile_path)
        data['profile_picture'] = profile_filename
        resize_image(profile_path)

    # Handle social media and products/services
    data['social_media'] = json.loads(data.get('social_media', '[]'))
    data['products_services'] = json.loads(data.get('products_services', '[]'))

    # Generate unique URL for the card
    card_id = str(uuid.uuid4())
    card_url = url_for('get_card', card_id=card_id, _external=True)
    data['card_url'] = card_url
    app.logger.info(f"Generated card URL: {card_url}")

    # Save card data to database
    new_card = BusinessCard(
        first_name=data['firstName'],
        last_name=data['lastName'],
        job_title=data['jobTitle'],
        email=data['email'],
        phone=data['phone'],
        logo=data.get('logo'),
        profile_picture=data.get('profile_picture'),
        social_media=data['social_media'],
        products_services=data['products_services'],
        card_url=card_url
    )
    db.session.add(new_card)
    db.session.commit()
    app.logger.info(f"New card created: {new_card}")

    return jsonify({
        "success": True,
        "message": "Digital Business Card created successfully",
        "card_url": card_url
    })

@app.route('/card/<card_id>', methods=['GET'])
def get_card(card_id):
    app.logger.info(f"Fetching card with id: {card_id}")
    card = BusinessCard.query.filter_by(card_url=url_for('get_card', card_id=card_id, _external=True)).first()
    if card:
        app.logger.info(f"Card found: {card}")
        return render_template('view-card.html', card=card)
    else:
        app.logger.error("Card not found")
        return "Card not found", 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-card.html')
@login_required
def create_card_page():
    return render_template('create-card.html')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    with app.app_context():
        db.create_all()
    app.run(debug=True)