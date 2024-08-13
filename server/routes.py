from flask import request, jsonify
from server import app, db
from server.models import PersonalDetails, ContactUs

# Index Route
@app.route("/")
def index():
    return "Welcome to Hadkaur Fitness API!"

# Route to submit personal details (POST)
@app.route("/personal_details", methods=["POST"])
def submit_personal_details():
    data = request.get_json()
    try:
        required_fields = ['first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'height', 'weight', 'goal', 'gender', 'activity_factor']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        personal_details = PersonalDetails(**data)
        db.session.add(personal_details)
        db.session.commit()
        return jsonify({"message": "Personal details submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get all personal details (GET)
@app.route("/personal_details", methods=["GET"])
def get_personal_details():
    details = PersonalDetails.query.all()
    return jsonify([detail.to_dict() for detail in details])

# Route to get personal details by ID (GET)
@app.route("/personal_details/<int:id>", methods=["GET"])
def get_personal_detail(id):
    detail = PersonalDetails.query.get(id)
    if detail:
        return jsonify(detail.to_dict())
    else:
        return jsonify({"error": "Personal details not found"}), 404

# Route to update personal details by ID (PUT)
@app.route("/personal_details/<int:id>", methods=["PUT"])
def update_personal_detail(id):
    data = request.get_json()
    detail = PersonalDetails.query.get(id)
    if detail:
        for key, value in data.items():
            setattr(detail, key, value)
        db.session.commit()
        return jsonify({"message": "Personal details updated successfully"})
    else:
        return jsonify({"error": "Personal details not found"}), 404

# Route to delete personal details by ID (DELETE)
@app.route("/personal_details/<int:id>", methods=["DELETE"])
def delete_personal_detail(id):
    detail = PersonalDetails.query.get(id)
    if detail:
        db.session.delete(detail)
        db.session.commit()
        return jsonify({"message": "Personal details deleted successfully"})
    else:
        return jsonify({"error": "Personal details not found"}), 404

# Route to submit contact us message (POST)
@app.route("/contact_us", methods=["POST"])
def submit_contact_us():
    data = request.get_json()
    try:
        required_fields = ['name', 'email', 'phone', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        contact_us = ContactUs(**data)
        db.session.add(contact_us)
        db.session.commit()
        return jsonify({"message": "Contact us message submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get all contact messages (GET)
@app.route("/contact_us", methods=["GET"])
def get_contact_messages():
    messages = ContactUs.query.all()
    return jsonify([message.to_dict() for message in messages])

# Route to get contact message by ID (GET)
@app.route("/contact_us/<int:id>", methods=["GET"])
def get_contact_message(id):
    message = ContactUs.query.get(id)
    if message:
        return jsonify(message.to_dict())
    else:
        return jsonify({"error": "Contact message not found"}), 404

# Route to update contact message by ID (PUT)
@app.route("/contact_us/<int:id>", methods=["PUT"])
def update_contact_message(id):
    data = request.get_json()
    message = ContactUs.query.get(id)
    if message:
        for key, value in data.items():
            setattr(message, key, value)
        db.session.commit()
        return jsonify({"message": "Contact message updated successfully"})
    else:
        return jsonify({"error": "Contact message not found"}), 404

# Route to delete contact message by ID (DELETE)
@app.route("/contact_us/<int:id>", methods=["DELETE"])
def delete_contact_message(id):
    message = ContactUs.query.get(id)
    if message:
        db.session.delete(message)
        db.session.commit()
        return jsonify({"message": "Contact message deleted successfully"})
    else:
        return jsonify({"error": "Contact message not found"}), 404

