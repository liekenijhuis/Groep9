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

# Basis chart (polygon + punten)
radar = (
    alt.Chart(closed_data)
    .mark_line(closed=True, strokeWidth=2, color="steelblue")
    .encode(x="x:Q", y="y:Q")
    + alt.Chart(closed_data)
    .mark_point(filled=True, color="steelblue", size=60)
    .encode(x="x:Q", y="y:Q", tooltip=["Factor", "Score"])
)

# Labels toevoegen op de rand
labels = (
    alt.Chart(mean_scores)
    .mark_text(align="center", baseline="middle", fontSize=12)
    .encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        text="Factor"
    )
)

# Samenvoegen
final_chart = (radar + labels).properties(
    title="Gemiddelde scores per factor (Radar Chart)",
    width=600,
    height=600
)

# Tonen in Streamlit
st.altair_chart(final_chart, use_container_width=True)
