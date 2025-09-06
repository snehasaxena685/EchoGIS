# EchoGIS_app.py
import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime

# ---------------------------
# Page configuration
# ---------------------------
st.set_page_config(page_title="EchoGIS - Prototype", layout="wide")
st.title("EchoGIS — Prototype Dashboard (Demo)")

# ---------------------------
# Password protection
# ---------------------------
DEFAULT_PASSWORD = "Dolphin2025"

# Try loading from secrets.toml, else fallback
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
            st.rerun()   # modern Streamlit rerun
        else:
            st.error("❌ Incorrect password. Contact author for access.")
    st.stop()

# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.title("⚙️ EchoGIS Controls")
st.sidebar.markdown("Adjust prototype demo parameters here.")

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
# Time filter (convert to Python datetime)
# ---------------------------
min_t = df["timestamp"].min().to_pydatetime()
max_t = df["timestamp"].max().to_pydatetime()

time_val = st.sidebar.slider(
    "Show data up to:",
    min_value=min_t,
    max_value=max_t,
    value=max_t,
    format="YYYY-MM-DD HH:mm:ss"
)

df_shown = df[df["timestamp"] <= pd.to_datetime(time_val)].copy()

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
    """Ray casting algorithm to check if a point is inside polygon"""
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

# Colors
color_map = {"Safe": [0, 128, 255], "Danger": [255, 0, 0]}
df_shown["color"] = df_shown["status"].map(lambda s: color_map.get(s, [0, 0, 0]))

# ---------------------------
# Pydeck map layers
# ---------------------------
dolphin_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_shown,
    get_position='[longitude, latitude]',
    get_color="color",
    get_radius=60,
    pickable=True
)

polygon_layer = pdk.Layer(
    "PolygonLayer",
    data=[{"coordinates": [[c[::-1] for c in danger_polygon]]}],
    get_polygon="coordinates",
    stroked=True,
    filled=False,
    get_line_color=[255, 0, 0],
    line_width_min_pixels=2
)

view_state = pdk.ViewState(
    longitude=df["longitude"].mean(),
    latitude=df["latitude"].mean(),
    zoom=12,
    pitch=0
)

deck = pdk.Deck(
    layers=[dolphin_layer, polygon_layer],
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
- This is a demo with **simulated dolphin data**. Replace with real detections when available.
- Password protection is enabled for ethical safety.
- Next steps: integrate **Sentinel-2 imagery, CPCB water quality data, and real-time alerting (SMS/Email/AI analytics)**.
""")
