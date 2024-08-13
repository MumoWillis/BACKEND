from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

class PersonalDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    goal = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    activity_factor = db.Column(db.String(20), nullable=False)

class ContactUs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(500), nullable=False)

@app.route('/personal_details', methods=['POST'])
def submit_personal_details():
    data = request.get_json()
    personal_details = PersonalDetails(**data)
    db.session.add(personal_details)
    db.session.commit()
    return jsonify({"message": "Personal details submitted successfully"})

@app.route('/contact_us', methods=['POST'])
def submit_contact_us():
    data = request.get_json()
    contact_us = ContactUs(**data)
    db.session.add(contact_us)
    db.session.commit()
    return jsonify({"message": "Contact us message submitted successfully"})

if __name__ == "__main__":
    app.run(debug=True)

