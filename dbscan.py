import requests
import json

# API Configuration
API_URL = "http://192.168.0.144:2612/azp"  # Change this to your actual API URL if hosted remotely
API_KEY = "azp-261211102024-aquadrox"  # Your API Key

def fetch_data_from_api(limit=5, project=None):
    """Retrieve stored data from the API."""
    headers = {"X-API-KEY": API_KEY}  # Authentication header
    params = {}  # Query parameters

    if project:
        params["project"] = project  # Optional project filter

    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad status codes

        data = response.json()
        if not data:
            print("⚠️ No data found.")
            return

        print("\n📊 Retrieved Data from API:")
        for record in data:
            print(f"\n🆔 ID: {record['id']}")
            print(f"📅 Timestamp: {record['timestamp']}")
            print(f"🏗️ Project: {record['project']}")
            try:
                parsed_data = json.loads(record["data"])  # Try to format JSON data
                print(f"📡 Data: {json.dumps(parsed_data, indent=2)}")
            except json.JSONDecodeError:
                print(f"📡 Data: {record['data']}")  # Print as is if not JSON
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    fetch_data_from_api()  # Adjust limit as needed
