from flask import Flask
from models import User, db, bcrypt
from routes import create_auth_blueprint
from flask_login import LoginManager
from config import Config
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)
oauth = OAuth(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Set up global CORS to allow all routes
CORS(app, resources={r"*": {"origins": "http://127.0.0.1:5173"}}, supports_credentials=True)

# Create and register the blueprint
auth_blueprint = create_auth_blueprint(oauth)
app.register_blueprint(auth_blueprint, url_prefix='/api')  # Prefix all routes with /api

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return 'Welcome to the Flask App!'

# Correct conditional check for main
if __name__ == '_main_':
    app.run(debug=True)