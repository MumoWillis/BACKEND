from app import create_app
from models import db, Contact

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()

    # Seed data
    if not Contact.query.first():  # Check if table is empty
        contact1 = Contact(name='John Doe', email='john@example.com', phone='555-555-5555', message='Hello, this is a test message.')
        contact2 = Contact(name='Jane Smith', email='jane@example.com', phone='555-555-5556', message='Another test message.')
        
        db.session.add(contact1)
        db.session.add(contact2)
        db.session.commit()
        print("Database seeded!")
    else:
        print("Database already seeded.")

