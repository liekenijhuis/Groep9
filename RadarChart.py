import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Data inladen
df = pd.read_csv("airline_passenger_satisfaction.csv")

# Kolommen die meegenomen worden voor de radar chart
factors = [
    "Departure and Arrival Time Convenience","Ease of Online Booking","Check-in Service","Online Boarding",
    "Gate Location","On-board Service","Seat Comfort","Leg Room Service","Cleanliness",
    "Food and Drink","In-flight Service","In-flight Wifi Service",
    "In-flight Entertainment","Baggage Handling"
]

# Gemiddelde scores berekenen
mean_scores = df[factors].mean().values

# Radar chart voorbereiden
N = len(factors)
angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
scores = mean_scores.tolist()
scores += scores[:1]  # polygon sluiten
angles += angles[:1]  # polygon sluiten

# Plot maken
fig, ax = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))

# Lijn + vulling
ax.plot(angles, scores, color="teal", linewidth=2)
ax.fill(angles, scores, color="teal", alpha=0.25)

# Stippen bij elke score
ax.scatter(angles, scores, color="teal", s=40, zorder=5)

# Tekstlabels iets verder buiten de stippen
for angle, score, factor in zip(angles, scores, factors + [factors[0]]):
    ax.text(angle, score + 0.3, f"{score:.1f}", 
            ha="center", va="center", fontsize=8, color="black")

# Labels rond de cirkel
#ax.set_xticks(angles[:-1])
#ax.set_xticklabels(factors, fontsize=8)

# Y-as schaal forceren: 0 in het midden, 5 aan de rand
#ax.set_ylim(0, 5)

# Labels rond de cirkel iets verder naar buiten plaatsen
label_offset = 0.3  # afstand buiten de cirkel
for angle, factor in zip(angles[:-1], factors):
    x = np.cos(angle) * (5 + label_offset)  # 5 is de max van de y-as
    y = np.sin(angle) * (5 + label_offset)
    ax.text(x, y, factor, ha="center", va="center", fontsize=8)
    
# Verberg standaard xticklabels
ax.set_xticks([])



# Rasters en schaal aanpassen
ax.set_rlabel_position(30)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=7, color="gray")
ax.grid(color="lightgray", linestyle="--")

# Titel
plt.title("Gemiddelde scores per factor (Radar Chart)", size=12, pad=20)

# Tonen in Streamlit
st.pyplot(fig)
