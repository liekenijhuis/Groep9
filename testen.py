import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd


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
plt.figure(figsize=(8,6))
scatter = plt.scatter(
    satis["Arrival Delay"], 
    satis["Departure Delay"], 
    c=satis["rating"], 
    cmap="jet", 
    alpha=0.4
)

plt.colorbar(scatter, label="Average Rating")
plt.xlabel("Arrival Delay (minuten)")
plt.ylabel("Departure Delay (minuten)")
plt.title("Scatterplot van Arrival vs Departure Delay, gekleurd op Rating")
plt.show()


## 1 slider met twee punten voor de leeftijd (nog niet getest)
st.markdown("### Leeftijdsfilter")
st.write("Pas hier de minimale en maximale leeftijd aan.")
st.write("Let op! Zorg dat de maximale leeftijd niet kleiner is dan de minimale leeftijd!")

# Eén range slider
age_range = st.slider(
    "Leeftijdsbereik",
    int(df["Age"].min()),
    int(df["Age"].max()),
    (int(df["Age"].min()), int(df["Age"].max())),  # startwaarden: min en max
    key="age_range_slider"
)

# min en max apart beschikbaar
min_age, max_age = age_range