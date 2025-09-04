import os
import requests
from datetime import datetime
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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

#violin and whisker plot for the pollutants

def _ensure_graphs_directory() -> str:
    base_dir = os.path.dirname(__file__)
    graphs_dir = os.path.join(base_dir, "static", "graphs")
    os.makedirs(graphs_dir, exist_ok=True)
    return graphs_dir


def _safe_state_slug(state_name: str) -> str:
    return (_normalize_state_for_api(state_name) or "state").lower()


def generate_state_pollutant_distribution_plot(state_name: str, records: list[dict]) -> str:
    """
    Generate a composite plot (violin + jitter and horizontal boxen) showing
    distribution of avg_value by pollutant for the given state's records.

    The image is saved to static/graphs/<state>.png and overwritten on each call.
    Returns the relative path under the Flask static folder, e.g. "graphs/delhi.png".

    Note: The visualization is independent of any timestamp columns, so changes
    in time-related fields won't alter the plot structure itself.
    """

    graphs_dir = _ensure_graphs_directory()
    state_slug = _safe_state_slug(state_name)
    output_filename = f"{state_slug}.png"
    output_path = os.path.join(graphs_dir, output_filename)

    # Build DataFrame from records
    df = pd.DataFrame.from_records(records or [])
    if df.empty or "avg_value" not in df.columns or "pollutant_id" not in df.columns:
        # Create an empty placeholder figure
        plt.figure(figsize=(10, 4))
        plt.text(0.5, 0.5, "No data available", ha="center", va="center")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close()
        return os.path.join("graphs", output_filename).replace("\\", "/")

    # Coerce numeric and drop missing
    df = df.copy()
    df["avg_value"] = pd.to_numeric(df["avg_value"], errors="coerce")
    df = df.dropna(subset=["avg_value"]) 

    sns.set_theme(style="whitegrid", context="notebook")

    # Create composite figure with two subplots
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(14, 5))

    # Left: Violin + jitter
    ax1 = axes[0]
    if not df.empty:
        sns.violinplot(data=df, x="pollutant_id", y="avg_value", inner="quartile", cut=0, scale="width", ax=ax1)
        sns.stripplot(data=df, x="pollutant_id", y="avg_value", color="black", alpha=0.25, jitter=0.25, size=2, ax=ax1)
        ax1.set_title(f"Distribution by pollutant (violin + jitter) for {state_name}")
        ax1.set_xlabel("Pollutant")
        ax1.set_ylabel("Average Value")
        for label in ax1.get_xticklabels():
            label.set_rotation(30)
            label.set_ha("right")

    # Right: Horizontal boxen
    ax2 = axes[1]
    if not df.empty:
        sns.boxenplot(data=df, y="pollutant_id", x="avg_value", orient="h", ax=ax2)
        ax2.set_title(f"Whisker plot for {state_name}")
        ax2.set_xlabel("Average Value")
        ax2.set_ylabel("Pollutant")

    fig.tight_layout()
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    # Return path relative to static folder
    return os.path.join("graphs", output_filename).replace("\\", "/")




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