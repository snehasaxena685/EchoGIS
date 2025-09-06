# make_mock_dolphins.py
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

n_dolphins = 3
n_steps = 60
start_time = datetime(2025, 9, 5, 6, 0, 0)  # arbitrary start
lats = np.linspace(25.250, 25.330, n_steps)
lons = np.linspace(86.980, 87.050, n_steps)

rows = []
for d in range(1, n_dolphins+1):
    lat_offset = (d-2) * 0.0025
    lon_offset = (d-2) * -0.002
    for i in range(n_steps):
        ts = start_time + timedelta(minutes=i)
        lat = float(lats[i] + lat_offset + np.random.normal(0, 0.0005))
        lon = float(lons[i] + lon_offset + np.random.normal(0, 0.0005))
        rows.append({
            "dolphin_id": f"D{d:02d}",
            "timestamp": ts.isoformat(),
            "latitude": lat,
            "longitude": lon
        })

df = pd.DataFrame(rows)
df.to_csv("echogis_mock_dolphins.csv", index=False)
print("Created echogis_mock_dolphins.csv with", len(df), "rows")
