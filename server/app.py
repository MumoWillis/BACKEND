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

@app.route('/contact-us', methods=['GET', 'POST', 'PUT', 'DELETE'])
def contact_us():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400
        try:
            contact = ContactUs(
                name=data.get('name'),
                email=data.get('email'),
                phone=data.get('phone'),
                message=data.get('message')
            )
            db.session.add(contact)
            db.session.commit()
            return jsonify({"message": "Contact us message submitted successfully"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"An error occurred: {e}"}), 500

    elif request.method == 'GET':
        try:
            contacts = ContactUs.query.all()
            results = [contact.to_dict() for contact in contacts]
            return jsonify(results), 200
        except Exception as e:
            return jsonify({"message": f"An error occurred: {e}"}), 500

    elif request.method == 'PUT':
        data = request.get_json()
        contact_id = data.get('id')
        if not contact_id:
            return jsonify({"message": "Contact ID is required"}), 400
        try:
            contact = ContactUs.query.get(contact_id)
            if contact:
                contact.name = data.get('name', contact.name)
                contact.email = data.get('email', contact.email)
                contact.phone = data.get('phone', contact.phone)
                contact.message = data.get('message', contact.message)
                db.session.commit()
                return jsonify({"message": "Contact us message updated successfully"}), 200
            else:
                return jsonify({"message": "Contact us message not found"}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"An error occurred: {e}"}), 500

    elif request.method == 'DELETE':
        data = request.get_json()
        contact_id = data.get('id')
        if not contact_id:
            return jsonify({"message": "Contact ID is required"}), 400
        try:
            contact = ContactUs.query.get(contact_id)
            if contact:
                db.session.delete(contact)
                db.session.commit()
                return jsonify({"message": "Contact us message deleted successfully"}), 200
            else:
                return jsonify({"message": "Contact us message not found"}), 404
        except Exception as e:
            db.session.rollback()
            return jsonify({"message": f"An error occurred: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True)


