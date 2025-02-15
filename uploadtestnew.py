import requests
import datetime
import json
import random
import time

# 🔐 API Configuration
API_URL = "http://192.168.0.144:2612/loura-marine"  # Replace with your actual API URL
API_KEY = "azp-261211102024-aquadrox"  # 🔑 Use your actual API key

def generate_random_data():
    """Generate random data for sensors."""
    timestamp = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

    sensors = {
        "AZP-1": random.uniform(-10, 10),
        "AZP-2": random.uniform(-10, 10),
        "AZP-3": random.uniform(-10, 10),
        "AZP-4": random.uniform(-10, 10),
    }

    data_batch = {
        key: {
            'value': f"{value:.2f} ppm",
            'timestamp': timestamp
        }
        for key, value in sensors.items()
    }

    return data_batch

def send_data_to_api():
    """Send random sensor data to the API."""
    data_batch = generate_random_data()

    payload = {
        "project": "smart-buoy",  # Define the project name
        "data": json.dumps(data_batch)
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": API_KEY  # 🔐 Include API Key
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"✅ Data successfully sent to API: {json.dumps(data_batch, indent=2)}")
        else:
            print(f"⚠️ Failed to send data! Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending data: {e}")

if __name__ == "__main__":
    try:
        while True:
            send_data_to_api()
            print("⏳ Waiting for 30 seconds before sending the next batch...")
            time.sleep(30)
    except KeyboardInterrupt:
        print("🚪 Program terminated by user.")
