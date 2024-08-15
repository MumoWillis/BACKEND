from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)  # Initialize CORS

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=False)

@app.route('/contact-us', methods=['POST'])
def contact_us():
    if not request.is_json:
        return jsonify({'message': 'Content-Type must be application/json'}), 415

    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    message = data.get('message')

    if not all([name, email, message]):
        return jsonify({'message': 'Missing required fields'}), 400

    new_contact = Contact(name=name, email=email, phone=phone, message=message)
    db.session.add(new_contact)
    db.session.commit()

    return jsonify({'message': 'Message sent successfully!'}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables if they do not exist
    app.run(debug=True)





