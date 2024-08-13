
from flask_sqlalchemy import SQLAlchemy
from flask import Flask



app = Flask(__name__)
db = SQLAlchemy()


class PersonalDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    goal = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    activity_factor = db.Column(db.String(20), nullable=False)
    bmi = db.Column(db.Float, nullable=True)
    bmr = db.Column(db.Float, nullable=True)
    tdee = db.Column(db.Float, nullable=True)
    recommended_calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat(),  # Format for JSON serialization
            'height': self.height,
            'weight': self.weight,
            'goal': self.goal,
            'gender': self.gender,
            'activity_factor': self.activity_factor,
            'bmi': self.bmi,
            'bmr': self.bmr,
            'tdee': self.tdee,
            'recommended_calories': self.recommended_calories,
            'protein': self.protein,
            'fat': self.fat,
            'carbs': self.carbs
        }

class ContactUs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(500), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'message': self.message
        }
