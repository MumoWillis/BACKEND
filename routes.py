from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, bcrypt
from authlib.integrations.flask_client import OAuth

def create_auth_blueprint(oauth):
    auth = Blueprint('auth', __name__)  # Corrected from _name to __name_

    google = oauth.register(
        name='google',
        client_id='your_google_client_id',
        client_secret='your_google_client_secret',
        access_token_url='https://accounts.google.com/o/oauth2/token',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'email'},
    )

    @auth.route('/signup', methods=['POST'])
    def signup():
        print("Signup route accessed")  # Debugging line
        data = request.get_json()
        existing_user = User.query.filter_by(email=data['email']).first()

        if existing_user:
            return jsonify({'message': 'User already exists!'}), 409

        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], email=data['email'], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Account created successfully!'}), 201

    @auth.route('/login', methods=['POST'])
    def login():
        print("Login route accessed")  # Debugging line
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        if user and bcrypt.check_password_hash(user.password, data['password']):
            login_user(user)
            return jsonify({'message': 'Login successful!'})
        else:
            return jsonify({'message': 'Invalid credentials!'}), 401

    @auth.route('/logout', methods=['POST'])
    @login_required
    def logout():
        print("Logout route accessed")  # Debugging line
        logout_user()
        return jsonify({'message': 'Logged out successfully!'})

    @auth.route('/login/google')
    def login_google():
        print("Google login route accessed")  # Debugging line
        redirect_uri = url_for('auth.authorized', _external=True)
        return google.authorize_redirect(redirect_uri)

    @auth.route('/login/google/authorized')
    def authorized():
        print("Google authorized route accessed")  # Debugging line
        token = google.authorize_access_token()
        if token is None:
            return 'Access denied: error={} description={}'.format(
                request.args.get('error'),
                request.args.get('error_description')
            )
        
        user_info = google.get('userinfo').json()
        email = user_info['email']
        user = User.query.filter_by(email=email).first()
        
        if not user:
            user = User(username=email.split('@')[0], email=email)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        # Store the token in session
        session['google_token'] = token

        return redirect(url_for('index'))

    return auth