import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from AQI import get_available_states, fetch_realtime_aqi
import folium
from folium.plugins import MarkerCluster, BeautifyIcon


# AQI helpers adapted from your dashboard logic
def _get_pollutant_aqi(pollutant: str, value: float):
    breakpoints = {
        "PM2.5": [(0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200), (91, 120, 201, 300), (121, 250, 301, 400), (251, 1000, 401, 500)],
        "PM10": [(0, 50, 0, 50), (51, 100, 51, 100), (101, 250, 101, 200), (251, 350, 201, 300), (351, 430, 301, 400), (431, 1000, 401, 500)],
        "NO2": [(0, 40, 0, 50), (41, 80, 51, 100), (81, 180, 101, 200), (181, 280, 201, 300), (281, 400, 301, 400), (401, 1000, 401, 500)],
        "CO": [(0, 1, 0, 50), (1.1, 2, 51, 100), (2.1, 10, 101, 200), (10.1, 17, 201, 300), (17.1, 34, 301, 400), (34.1, 1000, 401, 500)],
        "OZONE": [(0, 50, 0, 50), (51, 100, 51, 100), (101, 168, 101, 200), (169, 208, 201, 300), (209, 748, 301, 400), (749, 1000, 401, 500)],
        "SO2": [(0, 40, 0, 50), (41, 80, 51, 100), (81, 380, 101, 200), (381, 800, 201, 300), (801, 1600, 301, 400), (1601, 10000, 401, 500)],
        "NH3": [(0, 200, 0, 50), (201, 400, 51, 100), (401, 800, 101, 200), (801, 1200, 201, 300), (1201, 1800, 301, 400), (1801, 10000, 401, 500)],
    }
    if pollutant not in breakpoints:
        return None
    for bp in breakpoints[pollutant]:
        clow, chigh, ilow, ihigh = bp
        if clow <= value <= chigh:
            return round(((ihigh - ilow) / (chigh - clow)) * (value - clow) + ilow)
    return None


def _aqi_category(aqi: int | None):
    if aqi is None:
        return "unknown"
    if aqi <= 50:
        return "good"
    if aqi <= 100:
        return "satisfactory"
    if aqi <= 200:
        return "moderate"
    if aqi <= 300:
        return "poor"
    if aqi <= 400:
        return "very-poor"
    return "severe"


app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    states = sorted(get_available_states())
    return render_template("index.html", states=states)


@app.route('/results', methods=['POST'])
def results():
    selected_state = (request.form.get('state') or '').strip()
    if not selected_state:
        return redirect(url_for('index'))

    raw = fetch_realtime_aqi(selected_state)

    # Enrich rows with AQI numbers and categories for styling
    data = []
    for r in raw:
        try:
            value = float(r.get("avg_value")) if r.get("avg_value") not in (None, "") else None
        except ValueError:
            value = None
        pollutant = (r.get("pollutant_id") or "").upper()
        aqi = _get_pollutant_aqi(pollutant, value) if value is not None else None
        category = _aqi_category(aqi)
        data.append({
            **r,
            "aqi": aqi,
            "aqi_category": category,
        })

    # Build Folium map
    coords = []
    for r in data:
        try:
            lat = float(r.get("latitude")) if r.get("latitude") not in (None, "") else None
            lon = float(r.get("longitude")) if r.get("longitude") not in (None, "") else None
        except ValueError:
            lat, lon = None, None
        if lat is not None and lon is not None:
            coords.append((lat, lon, r))

    # Default center (India) if no coordinates
    center_lat, center_lon = (20.5937, 78.9629)
    if coords:
        # Average center
        center_lat = sum(c[0] for c in coords) / len(coords)
        center_lon = sum(c[1] for c in coords) / len(coords)

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="OpenStreetMap")
    cluster = MarkerCluster().add_to(fmap)

    def marker_color(category: str) -> str:
        return {
            "good": "#009865",
            "satisfactory": "#FFDE33",
            "moderate": "#FF9933",
            "poor": "#CC0033",
            "very-poor": "#660099",
            "severe": "#7E0023",
        }.get(category, "#1D4ED8")

    for lat, lon, r in coords:
        popup = folium.Popup(
            html=f"<b>{r.get('station','')}</b><br>Pollutant: {r.get('pollutant_id','')}<br>AQI: {r.get('aqi','-')}<br>Avg: {r.get('avg_value','-')}<br>Updated: {r.get('last_update','-')}",
            max_width=300,
        )
        color = marker_color(r.get("aqi_category"))
        icon = BeautifyIcon(
            icon_shape='marker',
            number=str(r.get('aqi')) if r.get('aqi') is not None else '',
            border_color=color,
            text_color='#ffffff',
            background_color=color,
            spin=False,
        )
        folium.Marker(
            location=[lat, lon],
            icon=icon,
            tooltip=r.get('station', ''),
            popup=popup,
        ).add_to(cluster)

    # Simple legend
    legend_html = f'''
     <div style="position: fixed; bottom: 24px; left: 24px; z-index:9999; background: white; padding: 10px 12px; border:1px solid #e5e7eb; border-radius: 8px; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
      <div style="font-weight:600; margin-bottom:6px;">AQI Categories</div>
      <div style="display:flex; align-items:center; gap:8px; margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; background:#009865; border-radius:2px;"></span> Good</div>
      <div style="display:flex; align-items:center; gap:8px; margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; background:#FFDE33; border-radius:2px;"></span> Satisfactory</div>
      <div style="display:flex; align-items:center; gap:8px; margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; background:#FF9933; border-radius:2px;"></span> Moderate</div>
      <div style="display:flex; align-items:center; gap:8px; margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; background:#CC0033; border-radius:2px;"></span> Poor</div>
      <div style="display:flex; align-items:center; gap:8px; margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; background:#660099; border-radius:2px;"></span> Very Poor</div>
      <div style="display:flex; align-items:center; gap:8px; margin:2px 0;"><span style="display:inline-block; width:12px; height:12px; background:#7E0023; border-radius:2px;"></span> Severe</div>
     </div>
    '''
    fmap.get_root().html.add_child(folium.Element(legend_html))

    map_html = fmap._repr_html_()

    return render_template('results.html', state=selected_state, data=data, map_html=map_html)


# JSON endpoints
@app.route('/api/states', methods=['GET'])
def api_states():
    return jsonify(sorted(get_available_states()))


@app.route('/api/aqi', methods=['GET'])
def api_aqi():
    state = (request.args.get('state') or '').strip()
    if not state:
        return jsonify({"error": "Missing required query parameter 'state'"}), 400

    data = fetch_realtime_aqi(state)
    return jsonify(data)


if __name__ == "__main__":
    debug_flag = os.getenv('FLASK_DEBUG', '1') == '1'
    app.run(debug=debug_flag)


