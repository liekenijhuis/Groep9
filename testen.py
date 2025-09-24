import streamlit as st
import pandas as pd
import plotly.express as px

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

# Leeftijdsfilter
st.markdown("### Leeftijdsfilter")
st.write("Pas hier de minimale en maximale leeftijd aan.")
st.write("Let op! Zorg dat de maximale leeftijd niet kleiner is dan de minimale leeftijd!")

age_range = st.slider(
    "Leeftijdsbereik",
    int(satis["Age"].min()),
    int(satis["Age"].max()),
    (int(satis["Age"].min()), int(satis["Age"].max())),  # startwaarden
    key="age_range_slider"
)

min_age, max_age = age_range

# Filter toepassen
filtered = satis[(satis["Age"] >= min_age) & (satis["Age"] <= max_age)]

# Scatterplot maken met Plotly
fig = px.scatter(
    filtered,
    x="Arrival Delay",
    y="Departure Delay",
    color="rating",
    color_continuous_scale="Jet",
    opacity=0.5,
    title="Scatterplot van Arrival vs Departure Delay, gekleurd op Rating",
    labels={
        "Arrival Delay": "Arrival Delay (minuten)",
        "Departure Delay": "Departure Delay (minuten)",
        "rating": "Average Rating"
    }
)

# Plot tonen in Streamlit
st.plotly_chart(fig, use_container_width=True)

st.write(f"Geselecteerde leeftijdsrange: {min_age} - {max_age}")
