## AQI Dashboard

A simple Flask-based dashboard to fetch and visualize Air Quality Index (AQI) data. It renders an interactive map and result views using `folium` and standard Flask templates.

### Features
- **Flask app** serving pages from `templates/` and static assets from `static/`
- **Interactive map** rendering (via `folium`)
- **Results page** with styled output

### Project Structure
```text
AQI_Dashboard/
  demo.ipynb
  requirements.txt
  flask/
    app.py          # Flask entrypoint
    AQI.py          # AQI-related logic/helpers
    templates/      # Jinja2 templates (base, index, results)
    static/         # CSS/JS assets
```

### Prerequisites
- Python 3.12+ recommended
- Windows PowerShell or any shell

### Setup (Windows PowerShell)
```powershell
cd AQI_Dashboard

# 1) Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install -r requirements.txt
```

If you prefer using the bundled `flask/env` environment that appears in the repo, you can instead activate it:
```powershell
.\flask\env\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run the App
```powershell
cd flask

# Option A: using Flask CLI
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"  # optional
flask run

# Option B: run directly
python app.py
```

The server will start on `http://127.0.0.1:5000` by default.

### Configuration
- If API keys or configuration are required later, place them in a `.env` file at the project root and load via `python-dotenv`. Example format:
```env
API_KEY=your_key_here
API_BASE_URL=https://example.com
```

### Notes
- Jupyter notebook `demo.ipynb` is included for experimentation or data exploration.
- For Linux/macOS shells, replace the activation and environment variable commands accordingly.

### License
This project is provided as-is for learning and demo purposes.


