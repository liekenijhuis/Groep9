import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

# Data inladen
df = pd.read_csv("airline_passenger_satisfaction.csv")

# Kolommen die meegenomen worden voor de radar chart
factors = [
    "Departure and Arrival Time Convenience","Ease of Online Booking","Check-in Service","Online Boarding",
    "Gate Location","On-board Service","Seat Comfort","Leg Room Service","Cleanliness",
    "Food and Drink","In-flight Service","In-flight Wifi Service",
    "In-flight Entertainment","Baggage Handling"
]

# Gemiddelde scores berekenen per factor
mean_scores = df[factors].mean().reset_index()
mean_scores.columns = ["Factor", "Score"]

# Voor radar chart: hoek berekenen
mean_scores["Angle"] = np.linspace(0, 2*np.pi, len(mean_scores), endpoint=False)

# Coördinaten berekenen
mean_scores["x"] = mean_scores["Score"] * np.cos(mean_scores["Angle"])
mean_scores["y"] = mean_scores["Score"] * np.sin(mean_scores["Angle"])

# Data sluiten zodat de lijn een cirkel vormt
closed_data = pd.concat([mean_scores, mean_scores.iloc[[0]]])

# Radar polygon + punten
radar_line = (
    alt.Chart(closed_data)
    .mark_line(strokeWidth=2, color="steelblue")
    .encode(x="x:Q", y="y:Q")
)

radar_points = (
    alt.Chart(closed_data)
    .mark_point(filled=True, color="steelblue", size=60)
    .encode(x="x:Q", y="y:Q", tooltip=["Factor", "Score"])
)

# Labels net buiten de cirkel zetten
label_offset = 0.3
labels = (
    alt.Chart(mean_scores.assign(
        lx=(mean_scores["Score"] + label_offset) * np.cos(mean_scores["Angle"]),
        ly=(mean_scores["Score"] + label_offset) * np.sin(mean_scores["Angle"])
    ))
    .mark_text(align="center", baseline="middle", fontSize=11)
    .encode(x="lx:Q", y="ly:Q", text="Factor")
)

# ✅ Rings fix: voor elke radius alle hoeken maken
angles = np.linspace(0, 2*np.pi, 200)
radii = [2, 4, 6]  # kies passend bij jouw schaal (1–5 of 1–10)
rings = pd.DataFrame([
    {"radius": r, "Angle": a, "x": r*np.cos(a), "y": r*np.sin(a)}
    for r in radii for a in angles
])

radar_grid = (
    alt.Chart(rings)
    .mark_line(strokeDash=[2,2], color="lightgray")
    .encode(x="x:Q", y="y:Q", detail="radius:N")
)

# Samenvoegen
final_chart = (radar_grid + radar_line + radar_points + labels).properties(
    title="Gemiddelde scores per factor (Radar Chart)",
    width=600,
    height=600
).configure_axis(grid=False, domain=False, ticks=False, labels=False)

# Tonen in Streamlit
st.altair_chart(final_chart, use_container_width=True)


