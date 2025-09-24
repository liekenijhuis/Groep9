import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

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

# Scatterplot maken
fig, ax = plt.subplots(figsize=(8,6))
scatter = ax.scatter(
    satis["Arrival Delay"], 
    satis["Departure Delay"], 
    c=satis["rating"], 
    cmap="jet", 
    alpha=0.4
)

cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label("Average Rating")
ax.set_xlabel("Arrival Delay (minuten)")
ax.set_ylabel("Departure Delay (minuten)")
ax.set_title("Scatterplot van Arrival vs Departure Delay, gekleurd op Rating")

# Plot tonen in Streamlit
st.pyplot(fig)

# Leeftijdsfilter
st.markdown("### Leeftijdsfilter")
st.write("Pas hier de minimale en maximale leeftijd aan.")
st.write("Let op! Zorg dat de maximale leeftijd niet kleiner is dan de minimale leeftijd!")

# Eén range slider (gebaseerd op Age uit satis)
age_range = st.slider(
    "Leeftijdsbereik",
    int(satis["Age"].min()),
    int(satis["Age"].max()),
    (int(satis["Age"].min()), int(satis["Age"].max())),  # startwaarden: min en max
    key="age_range_slider"
)

# min en max apart beschikbaar
min_age, max_age = age_range
st.write(f"Geselecteerde leeftijdsrange: {min_age} - {max_age}")
