# EchoGIS_app.py
import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import pydeck as pdk  # For custom map

# ---------------------------
# Page configuration
# ---------------------------
st.set_page_config(page_title="EchoGIS - Prototype", layout="wide")

# ---------------------------
# Custom Navbar (WII style)
# ---------------------------
def navbar():
    st.markdown(
        """
        <div style="background-color:#228B22;padding:10px;border-radius:5px;
                    display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:10px;">
                <img src="https://wii.gov.in/images/logo.png" width="250">
            </div>
            <h4 style="color:white;margin:0;">🌊 EchoGIS</h4>
        </div>
        """,
        unsafe_allow_html=True
    )
navbar()

st.title("Prototype to Protect Ganga Dolphin")

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
# Simple Danger Check
# ---------------------------
danger_polygon = [
    [87.010, 25.285],
    [87.040, 25.285],
    [87.040, 25.305],
    [87.010, 25.305]
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

# ---------------------------
# Dolphin Map with Clear Scatter
# ---------------------------
layers = []

# NDWI mock heatmap
if show_ndwi:
    ndwi_points = []
    for i in range(300):
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
        opacity=0.35
    )
    layers.append(ndwi_layer)

# Dolphin scatterplot
color_map = {"Safe": [0, 0, 255], "Danger": [255, 0, 0]}  # Blue & Red
df_shown["color"] = df_shown["status"].map(color_map)

dolphin_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_shown,
    get_position='[longitude, latitude]',
    get_color="color",
    get_radius=80,
    pickable=True,
)
layers.append(dolphin_layer)

# ---------------------------
# Easier Map Visualization (simple map)
# ---------------------------
st.subheader("🗺 Dolphin Tracking Map")

map_df = df_shown[["latitude", "longitude", "status"]].copy()
map_df["color"] = map_df["status"].map({"Safe": [0, 0, 255], "Danger": [255, 0, 0]})

st.map(map_df, latitude="latitude", longitude="longitude")

if show_ndwi:
    st.info("🌍 Sentinel-2 NDWI demo ON (showing mock water index heatmap).")

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
uploaded_file = st.file_uploader("Upload GIS Layer (Shapefile or GeoTIFF)", type=["shp", "tif"])
if uploaded_file:
    st.success(f"✅ Uploaded: {uploaded_file.name}")
    st.markdown("*(Demo placeholder — in real system this would overlay your QGIS data on the map)*")

# ---------------------------
# Recent positions table
# ---------------------------
st.subheader("📊 Recent Dolphin Positions")
st.dataframe(df_shown.sort_values("timestamp", ascending=False).head(20))

# ---------------------------
# Geofencing & Scatter Graph
# ---------------------------
st.subheader("🗺️ Scatter Graph with Geofence Alerts")

# Danger polygon (filled transparent red if danger exists)
fill_color = [255, 0, 0, 80] if counts.get("Danger", 0) > 0 else [255, 0, 0, 0]

polygon_layer = pdk.Layer(
    "PolygonLayer",
    data=[{"coordinates": [[c[::-1] for c in danger_polygon]]}],
    get_polygon="coordinates",
    stroked=True,
    filled=True,
    get_fill_color=fill_color,
    get_line_color=[255, 0, 0],
    line_width_min_pixels=3
)
layers.append(polygon_layer)

# Map view
view_state = pdk.ViewState(
    longitude=df["longitude"].mean(),
    latitude=df["latitude"].mean(),
    zoom=12,
    pitch=0
)

deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/satellite-streets-v11",
    tooltip={"text": "🐬 {status}\n📍 ({latitude}, {longitude})"}
)
st.pydeck_chart(deck)

# ---------------------------
# Footer notes
# ---------------------------
st.markdown("""
---
### Legend
🔵 Blue = Safe dolphin  
🔴 Red = Danger dolphin  
🟥 Transparent Red Polygon = High-risk canal/area (Geofence Alert)  
🌍 Green Heatmap = Sentinel-2 NDWI demo (mock water index)

---
### Notes
- Scatterplot is interactive with tooltips for each dolphin.
- ✅ NDWI layer simulates **Sentinel-2 water index**.
- 🛰️ QGIS upload highlights GIS workflow integration.
- 🚨 Geofence alert highlights danger zones dynamically.
- Password protection ensures ethical safety.
""")
