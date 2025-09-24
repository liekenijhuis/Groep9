import streamlit as st
import pandas as pd
import altair as alt

# Data inladen
satis = pd.read_csv("airline_passenger_satisfaction.csv")
flight = pd.read_csv("airlines_flights_data.csv")

# Kolommen die meegenomen worden voor de nieuwe rating
rating_cols = [
    "Ease of Online Booking","Check-in Service","Online Boarding","Gate Location",
    "On-board Service","Seat Comfort","Leg Room Service","Cleanliness",
    "Food and Drink","In-flight Service","In-flight Wifi Service",
    "In-flight Entertainment","Baggage Handling"
]

# Nieuwe kolom 'rating' toevoegen
satis["rating"] = satis[rating_cols].mean(axis=1)

# --- Leeftijdsfilter ---
st.markdown("### Leeftijdsfilter")
age_range = st.slider(
    "Leeftijdsbereik",
    int(satis["Age"].min()),
    int(satis["Age"].max()),
    (int(satis["Age"].min()), int(satis["Age"].max())),
    key="age_range_slider"
)
min_age, max_age = age_range

# --- Afstandsfilter ---
st.markdown("### Vlucht Afstand Filter")
distance_range = st.slider(
    "Afstandsbereik (Flight Distance)",
    int(satis["Flight Distance"].min()),
    int(satis["Flight Distance"].max()),
    (int(satis["Flight Distance"].min()), int(satis["Flight Distance"].max())),
    key="distance_range_slider"
)
min_dist, max_dist = distance_range

# Filter toepassen op leeftijd én afstand
filtered = satis[
    (satis["Age"] >= min_age) & (satis["Age"] <= max_age) &
    (satis["Flight Distance"] >= min_dist) & (satis["Flight Distance"] <= max_dist)
]

# Scatterplot met Altair
scatter = (
    alt.Chart(filtered)
    .mark_circle(opacity=0.4)
    .encode(
        x=alt.X("Arrival Delay", title="Arrival Delay (minuten)"),
        y=alt.Y("Departure Delay", title="Departure Delay (minuten)"),
        color=alt.Color("rating", scale=alt.Scale(scheme="turbo"), title="Average Rating"),
        tooltip=["Age", "Flight Distance", "Arrival Delay", "Departure Delay", "rating"]
    )
    .properties(
        title="Scatterplot van Arrival vs Departure Delay, gekleurd op Rating",
        width=700,
        height=500
    )
)

# Plot tonen in Streamlit
st.altair_chart(scatter, use_container_width=True)

# Extra info tonen
st.write(f"Geselecteerde leeftijdsrange: {min_age} - {max_age}")
st.write(f"Geselecteerde vlucht afstand: {min_dist} - {max_dist}")
