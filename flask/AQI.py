import os
import requests
from datetime import datetime
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# Load API key from environment
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Configure a requests Session with retries and backoff
_retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
_adapter = HTTPAdapter(max_retries=_retry_strategy)
_session = requests.Session()
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)
@lru_cache(maxsize=1)
def get_available_states():
    url = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": "10000"
    }

    if not API_KEY:
        raise RuntimeError("Missing API_KEY environment variable")

    response = _session.get(url, params=params, timeout=10)
    data = response.json()
    records = data.get("records", [])
    
    #counts= 0
    states = set()

    for record in records:
        state = record.get("state")
        if state:
            states.add(state)
    states = list(states)
    states_formated = []
    for i in states:
        j = i.replace("_"," ")
        states_formated.append(j)

 
            #counts += 1
    #print(f"Number of entries passed : {counts}") 
    return states_formated

    

def _normalize_state_for_api(state_name: str) -> str:
    # API expects underscores; UI shows spaces
    return (state_name or "").strip().replace(" ", "_")


def fetch_realtime_aqi(state_name):
    url = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"

    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": "100",
        "offset": "0",
        "filters[state]": _normalize_state_for_api(state_name)
    }

    if not API_KEY:
        raise RuntimeError("Missing API_KEY environment variable")

    response = _session.get(url, params=params, timeout=10)
    if response.status_code != 200:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []

    data = response.json()
    records = data.get("records", [])

    cleaned_data = []
    for record in records:
        cleaned_data.append({
            "station": record.get("station"),
            "pollutant_id": record.get("pollutant_id"),
            "avg_value": record.get("avg_value"),
            "last_update": record.get("last_update"),
            "latitude": record.get("latitude"),
            "longitude": record.get("longitude")
        })

    return cleaned_data

if __name__ == "__main__":
    state = input("Enter state name to fetch real-time AQI data: ").strip()
    pollutant_data = fetch_realtime_aqi(state)

    print(f"\nAQI details for {state} (fetched at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):\n")

    if not pollutant_data:
        print("No data found.")
    else:
        for entry in pollutant_data:
            print(f"Station: {entry['station']}")
            print(f"Pollutant: {entry['pollutant_id']}")
            print(f"Avg Value: {entry['avg_value']}")
            print(f"Last Update: {entry['last_update']}")
            print(f"Lat: {entry['latitude']}, Lon: {entry['longitude']}")
            print("-" * 40)
    t = get_available_states()
    for states in t :
        print(states)