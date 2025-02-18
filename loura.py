from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# -------------------------------
# 🔐 SECURITY CONFIGURATION
# -------------------------------
SECRET_API_KEY = os.getenv("SECRET_API_KEY", "azp-261211102024-aquadrox")  # Change manually or use env variable

# Database setup
DB_PATH = "./var/azp"
DB_NAME = f"{DB_PATH}/azp.db"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def init_db():
    """Initialize the database and ensure the required table exists."""
    try:
        os.makedirs(DB_PATH, exist_ok=True)  # Ensure the database directory exists

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS azp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT (datetime('now', '+8 hours')),  -- Force UTC-8
                    project TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            conn.commit()
        logging.info("✅ Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"❌ Database initialization failed: {e}")


init_db()  # Initialize DB on startup


# -------------------------------
# 🔐 API KEY VERIFICATION
# -------------------------------
def verify_api_key():
    """Check if the correct API key is provided in request headers."""
    api_key = request.headers.get("X-API-KEY")
    if api_key == SECRET_API_KEY:
        return True
    logging.warning("⚠️ Unauthorized API request detected!")
    return False


# -------------------------------
# 🚀 STORE DATA (POST)
# -------------------------------
@app.route('/loura-marine', methods=['POST'])
def store_sensor_data():
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 403  # 🔒 Reject unauthorized requests

    try:
        json_data = request.get_json()
        project = json_data.get("project", "unknown")  # Default if missing
        data = json_data.get("data", "")

        if not data:
            return jsonify({"error": "Data field cannot be empty"}), 400

        # Convert timestamps inside "data" to UTC-8
        try:
            data_dict = json.loads(data)  # Convert JSON string to dictionary
            for key, sensor_data in data_dict.items():
                if "timestamp" in sensor_data:
                    utc_time = datetime.strptime(sensor_data["timestamp"], "%Y-%m-%d %H:%M:%S")
                    sensor_data["timestamp"] = utc_time.strftime("%Y-%m-%d %H:%M:%S")
            data = json.dumps(data_dict)  # Convert back to JSON string
        except Exception as e:
            logging.warning(f"⚠️ Could not convert timestamp: {e}")

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO azp (project, data) VALUES (?, ?)", (project, data))
            conn.commit()
            last_id = cursor.lastrowid  # Get last inserted ID

        logging.info(f"✅ Data stored (UTC-8): ID={last_id}, Project={project}, Data={data}")

        # Verify if data is actually stored
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM azp WHERE id = ?", (last_id,))
            inserted_data = cursor.fetchone()
            if inserted_data:
                logging.info(f"✅ Verified Inserted Data: {inserted_data}")
            else:
                logging.error("❌ Data insertion verification failed!")

        return jsonify({"message": f"{project.capitalize()} data stored successfully", "id": last_id}), 201
    except Exception as e:
        logging.error(f"❌ Error storing data: {e}")
        return jsonify({"error": str(e)}), 500


# -------------------------------
# 📊 RETRIEVE DATA (GET)
# -------------------------------
@app.route('/azp', methods=['GET'])
def get_sensor_data():
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 403  # 🔒 Reject unauthorized requests

    try:
        sensor_type = request.args.get("project")  # Optional filter (lora/buoy)
        limit = request.args.get("limit", type=int)  # Optional limit

        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            if sensor_type:
                if limit:
                    cursor.execute("SELECT id, timestamp, project, data FROM azp WHERE project = ? ORDER BY timestamp DESC LIMIT ?", (sensor_type, limit))
                else:
                    cursor.execute("SELECT id, timestamp, project, data FROM azp WHERE project = ? ORDER BY timestamp DESC", (sensor_type,))
            else:
                if limit:
                    cursor.execute("SELECT id, timestamp, project, data FROM azp ORDER BY timestamp DESC LIMIT ?", (limit,))
                else:
                    cursor.execute("SELECT id, timestamp, project, data FROM azp ORDER BY timestamp DESC")
            data = cursor.fetchall()

        # Convert database timestamps to UTC-8 before sending
        data_fixed = []
        for row in data:
            utc_time = datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S")
            new_timestamp = utc_time.strftime("%Y-%m-%d %H:%M:%S")

            data_fixed.append({
                "id": row[0],
                "timestamp": new_timestamp,  # Return timestamp in UTC-8
                "project": row[2],
                "data": row[3],
            })

        logging.info(f"✅ Data retrieved (UTC-8): Project={sensor_type if sensor_type else 'ALL'}, Limit={limit if limit else 'NO LIMIT'}")
        return jsonify(data_fixed)
    except Exception as e:
        logging.error(f"❌ Error retrieving data: {e}")
        return jsonify({"error": str(e)}), 500


# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=2612, debug=True)
