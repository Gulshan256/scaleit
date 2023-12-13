from flask import Flask, jsonify
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required
import threading
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory H2 database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'  # Change this in a real application

db = SQLAlchemy(app)

# Define User and Role models for Flask-Security
class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

# Create tables
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Placeholder variables for CPU and replicas
cpu_utilization = 0.5
replicas = 1
replicas_lock = threading.Lock()  # Lock for synchronization

# Auto-scaling parameters
TARGET_CPU = 0.80
SLEEP_INTERVAL = 10  # Adjust as needed
MAX_REPLICAS_CHANGE = 50  # Maximum allowed change in replicas

# Route to update the replica count (requires authentication)
@app.route('/app/replicas', methods=['PUT'])
@login_required
def update_replicas():
    global replicas

    try:
        data = request.get_json()
        new_replicas = data.get('replicas', None)
        trigger_person = data.get('trigger_person', None)

        if new_replicas is None or not isinstance(new_replicas, int) or new_replicas < 1:
            return jsonify({"error": "Invalid replica count"}), 400

        with replicas_lock:
            # Check if the change in replicas is greater than 50
            if abs(new_replicas - replicas) > MAX_REPLICAS_CHANGE:
                # If the change is greater, require the trigger_person variable
                if trigger_person is None:
                    return jsonify({"error": "Trigger person is required for changes greater than 50 replicas"}), 400

            replicas = new_replicas

        return jsonify({"message": f"Replica count updated to {replicas} by {trigger_person}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Auto-scaling logic
def auto_scale():
    global cpu_utilization, replicas

    while True:
        # Simulate changing CPU utilization over time
        cpu_utilization += 0.05

        if cpu_utilization > TARGET_CPU:
            with replicas_lock:
                replicas = max(1, replicas - 1)
        else:
            with replicas_lock:
                replicas += 1

        print(f"Auto-scaling: CPU={cpu_utilization:.2f}, Replicas={replicas}")
        time.sleep(SLEEP_INTERVAL)


if __name__ == '__main__':
    # Start the auto-scaling logic in a separate thread
    auto_scale_thread = threading.Thread(target=auto_scale)
    auto_scale_thread.start()

    # Run the Flask app
    app.run(debug=True)
