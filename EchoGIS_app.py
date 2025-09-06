# EchoGIS_app.py
import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import numpy as np
from datetime import datetime
import base64

# ---------------------------
# Page configuration
# ---------------------------
st.set_page_config(page_title="EchoGIS - Prototype", layout="wide")

# ---------------------------
# Custom Navbar (WII style)
# ---------------------------
def navbar():st.markdown(
    """
    <div style="background-color:#228B22;padding:10px;border-radius:5px;
                display:flex;align-items:center;justify-content:space-between;">
        <div style="display:flex;align-items:center;gap:10px;">
            <img src="https://wii.gov.in/images/logo.png" width="250">
            <h2 style="color:white;margin:0;"></h2>
        </div>
        <h4 style="color:white;margin:0;">🌊 EchoGIS</h4>
    </div>
    """,
    unsafe_allow_html=True
)
navbar()

st.title(" Prototype to protect Ganga dolphin")

# ---------------------------
# Password protection
# ---------------------------
DEFAULT_PASSWORD = "Dolphin2025"
try:
    PASSWORD = st.secrets["APP_PASSWORD"]
except Exception:
    PASSWORD = DEFAULT_PASSWORD

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## 🔒 Secure Access — EchoGIS Prototype")
    pwd = st.text_input("Enter access password", type="password")
    if st.button("Enter"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password. Contact author for access.")
    st.stop()

# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.title("⚙️ EchoGIS Controls")
st.sidebar.markdown("Adjust prototype demo parameters here.")

# Sentinel NDWI mock toggle
show_ndwi = st.sidebar.checkbox("🌍 Show Sentinel-2 NDWI Layer (demo)", value=False)

# ---------------------------
# Load dolphin dataset
# ---------------------------
try:
    df = pd.read_csv("echogis_mock_dolphins.csv", parse_dates=["timestamp"])
except FileNotFoundError:
    st.error("CSV file 'echogis_mock_dolphins.csv' not found. Please generate it first.")
    st.stop()

df["timestamp"] = pd.to_datetime(df["timestamp"])

# ---------------------------
# Time filter + Timelapse
# ---------------------------
min_t = df["timestamp"].min().to_pydatetime()
max_t = df["timestamp"].max().to_pydatetime()

if "current_time" not in st.session_state:
    st.session_state.current_time = min_t

time_val = st.sidebar.slider(
    "⏳ Show data up to:",
    min_value=min_t,
    max_value=max_t,
    value=st.session_state.current_time,
    format="YYYY-MM-DD HH:mm:ss"
)

play = st.sidebar.checkbox("▶️ Play Time-lapse")

if play:
    unique_times = sorted(df["timestamp"].unique())
    try:
        idx = unique_times.index(pd.to_datetime(st.session_state.current_time))
    except ValueError:
        idx = 0
    next_idx = (idx + 1) % len(unique_times)
    st.session_state.current_time = unique_times[next_idx].to_pydatetime()
    time.sleep(0.3)
    st.rerun()
else:
    st.session_state.current_time = time_val

df_shown = df[df["timestamp"] <= pd.to_datetime(st.session_state.current_time)].copy()

# ---------------------------
# Danger polygon (near Bhagalpur demo zone)
# ---------------------------
danger_polygon = [
    [87.010, 25.285],
    [87.040, 25.285],
    [87.040, 25.305],
    [87.010, 25.305],
    [87.010, 25.285]
]

def point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i][0], poly[i][1]
        xj, yj = poly[j][0], poly[j][1]
        intersect = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
        )
        if intersect:
            inside = not inside
        j = i
    return inside

df_shown["status"] = df_shown.apply(
    lambda r: "Danger" if point_in_poly(r["longitude"], r["latitude"], danger_polygon) else "Safe",
    axis=1
)

color_map = {"Safe": [0, 128, 255], "Danger": [255, 0, 0]}
df_shown["color"] = df_shown["status"].map(lambda s: color_map.get(s, [0, 0, 0]))

# ---------------------------
# Pydeck map layers
# ---------------------------
layers = []

# NDWI Heatmap Layer (Mock Sentinel-2)
if show_ndwi:
    ndwi_points = []
    for i in range(200):
        ndwi_points.append({
            "longitude": df["longitude"].mean() + np.random.uniform(-0.05, 0.05),
            "latitude": df["latitude"].mean() + np.random.uniform(-0.05, 0.05),
            "value": np.random.uniform(-1, 1)
        })
    ndwi_layer = pdk.Layer(
        "HeatmapLayer",
        data=ndwi_points,
        get_position='[longitude, latitude]',
        get_weight="value",
        radiusPixels=80,
        opacity=0.4
    )
    layers.append(ndwi_layer)

# Dolphin layer
dolphin_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_shown,
    get_position='[longitude, latitude]',
    get_color="color",
    get_radius=60,
    pickable=True
)
layers.append(dolphin_layer)

# Danger polygon
polygon_layer = pdk.Layer(
    "PolygonLayer",
    data=[{"coordinates": [[c[::-1] for c in danger_polygon]]}],
    get_polygon="coordinates",
    stroked=True,
    filled=False,
    get_line_color=[255, 0, 0],
    line_width_min_pixels=2
)
layers.append(polygon_layer)

# View settings
view_state = pdk.ViewState(
    longitude=df["longitude"].mean(),
    latitude=df["latitude"].mean(),
    zoom=12,
    pitch=0
)

deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v10"
)
st.pydeck_chart(deck)

# ---------------------------
# Sidebar summary
# ---------------------------
st.sidebar.markdown("### 🐬 Dolphin Status Summary")
counts = df_shown["status"].value_counts().to_dict()
st.sidebar.write(counts)

if counts.get("Danger", 0) > 0:
    st.sidebar.error(f"⚠️ ALERT: {counts.get('Danger')} dolphin(s) in danger zone!")

# ---------------------------
# QGIS Skills Showcase
# ---------------------------
st.subheader("🛰️ QGIS Integration Demo")
st.markdown("Upload a **Shapefile (.shp)** or **GeoTIFF (.tif)** exported from QGIS to visualize here:")

uploaded_file = st.file_uploader("Upload GIS Layer", type=["shp", "tif"])

if uploaded_file:
    st.success(f"✅ Uploaded: {uploaded_file.name}")
    st.markdown("*(Demo placeholder — in real system this would overlay your QGIS data on the map)*")

# ---------------------------
# Recent positions table
# ---------------------------
st.subheader("📊 Recent Dolphin Positions")
st.dataframe(df_shown.sort_values("timestamp", ascending=False).head(20))

# ---------------------------
# Footer notes
# ---------------------------
st.markdown("""
---
### Notes
- This is a demo with **simulated dolphin data**.
- ✅ NDWI layer simulates **Sentinel-2 water index** (QGIS-ready).
- 🛰️ QGIS upload shows integration with **field GIS workflows**.
- Password protection is enabled for ethical safety.
""")
