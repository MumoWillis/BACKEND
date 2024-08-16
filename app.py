from flask import Flask, jsonify, request, session, Blueprint
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from config import Config

# Initialize the Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
metadata = MetaData()
db = SQLAlchemy(metadata=metadata)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# CORS configuration
CORS(app, resources={r"/api/*": {
    "origins": ["http://127.0.0.1:5173", "http://localhost:5173"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True
}})

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()

def _build_cors_preflight_response():
    response = jsonify({"message": "Preflight request handled"})
    response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin"))
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response, 200

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin"))
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response

@app.after_request
def after_request(response):
    return _corsify_actual_response(response)

# Root route
@app.route('/')
def index():
    return jsonify({'message': 'Welcome to the API!'})

# Auth Blueprint
auth = Blueprint('auth', __name__)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

# User signup
@auth.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    existing_user = User.query.filter_by(email=data['email']).first()

    if existing_user:
        return jsonify({'message': 'User already Exists!'}), 409

    new_user = User(username=data['username'], email=data['email'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Account created successfully!'}), 201

# User login
@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        session['user_id'] = user.id  # Storing the user's ID in session
        return jsonify({'message': 'Login successful!'})
    else:
        return jsonify({'message': 'Invalid credentials!'}), 401

# User logout
@auth.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  # Removing the user's ID from session
    return jsonify({'message': 'Logged out successfully!'})

# Register the auth blueprint
app.register_blueprint(auth, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)
