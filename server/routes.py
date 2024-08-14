from flask import request, jsonify
from . import app, db
from .models import ContactUs

@app.route('/contact-us', methods=['POST'])
def submit_contact_us():
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

@app.route('/contact-us', methods=['GET'])
def get_contact_messages():
    try:
        contacts = ContactUs.query.all()
        results = [contact.to_dict() for contact in contacts]
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

@app.route('/contact-us/<int:id>', methods=['GET'])
def get_contact_message(id):
    message = ContactUs.query.get(id)
    if message:
        return jsonify(message.to_dict())
    else:
        return jsonify({"message": "Contact message not found"}), 404

@app.route('/contact-us/<int:id>', methods=['PUT'])
def update_contact_message(id):
    data = request.get_json()
    message = ContactUs.query.get(id)
    if message:
        for key, value in data.items():
            setattr(message, key, value)
        db.session.commit()
        return jsonify({"message": "Contact message updated successfully"})
    else:
        return jsonify({"message": "Contact message not found"}), 404

@app.route('/contact-us/<int:id>', methods=['DELETE'])
def delete_contact_message(id):
    message = ContactUs.query.get(id)
    if message:
        db.session.delete(message)
        db.session.commit()
        return jsonify({"message": "Contact message deleted successfully"})
    else:
        return jsonify({"message": "Contact message not found"}), 404


