#import pandas as pd

# CSV-bestand inlezen
#df = pd.read_csv("duitse_automerken.csv")

# Controleren hoeveel unieke handelsbenamingen er zijn
#aantal_unieke = df["Handelsbenaming"].nunique()

#print(f"Aantal unieke handelsbenamingen: {aantal_unieke}")

# PKL-bestand inlezen
#df1 = pd.read_pickle("Elektrische_voertuigen_20251006.pkl")
#duitse_merken = [
#    "VOLKSWAGEN", "VW", "VOLKSWAGEN/ZIMNY", "FAW-VOLKSWAGEN",
#    "AUDI", "BMW", "BMW I", "MERCEDES-BENZ",
#    "OPEL", "PORSCHE", "FORD-CNG-TECHNIK"
#]
#duitse_voertuigen = df1[df1["Merk"].isin(duitse_merken)]
#unieke_handelsbenamingen = duitse_voertuigen["Handelsbenaming"].unique()

#print(f"Aantal unieke handelsbenamingen van Duitse merken: {len(unieke_handelsbenamingen)}")
#print(unieke_handelsbenamingen)
#print(df1.columns)

# Aantal unieke waarden in de kolom 'Handelsbenaming'
#aantal_unieke = df1["Handelsbenaming"].nunique()
#print(f"Aantal unieke handelsbenamingen: {aantal_unieke}")

# Optioneel: de unieke waarden zelf tonen
#unieke_waarden = df1["Handelsbenaming"].unique()
#print(unieke_waarden)

import pandas as pd
import streamlit as st
from sklearn.linear_model import LinearRegression
import numpy as np

# --- Data inladen ---
data = pd.read_csv("auto_types.csv")

# --- Definieer herkenningspatronen per type ---
def bepaal_type(merk, uitvoering):
    u = str(uitvoering).upper()
    m = str(merk).upper()

    # Elektrisch
    if "BMW I" in m or "PORSCHE" in m or u.startswith(("FA1FA1CZ", "3EER", "3EDF", "3EDE", "2EER", "2EDF", "2EDE", "E11", "0AW5", "QE2QE2G1", "QE1QE1G1", "HE1HE1G1")) or "EV" in u or "FA1FA1MD" in u:
        return "Elektrisch"
    # Diesel
    if "DIESEL" in u or "TDI" in u or "CDI" in u or "DPE" in u or u.startswith("D"):
        return "Diesel"
    # Benzine (default)
    return "Benzine"

# --- Type bepalen ---
data["Type"] = data.apply(lambda row: bepaal_type(row["Merk"], row["Uitvoering"]), axis=1)
st.write("Beschikbare brandstofcategorieën:", data["Type"].unique())

# --- Datum kolom ---
data["Datum eerste toelating"] = data["Datum eerste toelating"].astype(str).str.split(".").str[0]
data["Datum eerste toelating"] = pd.to_datetime(data["Datum eerste toelating"], format="%Y%m%d", errors="coerce")
data = data.dropna(subset=["Datum eerste toelating"])
data = data[data["Datum eerste toelating"].dt.year > 2010]
data["Maand"] = data["Datum eerste toelating"].dt.to_period("M").dt.to_timestamp()

# --- Aantal voertuigen per maand per type ---
maand_aantal = data.groupby(["Maand", "Type"]).size().unstack(fill_value=0)
cumulatief = maand_aantal.cumsum()

# --- Voorspelling tot 2030 ---
laatste_datum = cumulatief.index.max()
toekomst = pd.date_range(laatste_datum, "2030-12-31", freq="M")

# Voor elke brandstofsoort een lineair model fitten en voorspellen
voorspelling_df = pd.DataFrame(index=toekomst)

for col in cumulatief.columns:
    y = cumulatief[col].values
    X = np.arange(len(y)).reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)

    toekomst_X = np.arange(len(y), len(y) + len(toekomst)).reshape(-1, 1)
    voorspelling = model.predict(toekomst_X)
    voorspelling_df[col] = voorspelling

# Combineer historische + voorspelde data
totaal = pd.concat([cumulatief, voorspelling_df])

# --- Plotten ---
st.subheader("📈 Historische data + Voorspelling tot 2030")
st.line_chart(totaal)

# --- Extra info ---
st.write("Laatste bekende data:", cumulatief.tail())
st.write("Voorspelling (eerste maanden):", voorspelling_df.head())
