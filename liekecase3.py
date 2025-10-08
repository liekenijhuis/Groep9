import pandas as pd
import streamlit as st
import pickle

data = pd.read_csv("auto_types.csv")

# --- Definieer herkenningspatronen per type ---
def bepaal_type(merk, uitvoering):
    u = str(uitvoering).upper()
    m = str(merk).upper()

    # Elektrisch
    if "BMW I" in m or u.startswith("E11") or u.startswith("HE1HE1G1") or "EV" in u or "FA1FA1MD" in u or "FA1FA1CZ" in u or "HE1HE1G1" in u:
        return "Elektrisch"
    
    # Hybride
    if "HYBRID" in u or "PHEV" in u or "HYBRID" in m or "PLUG-IN" in u:
        return "Hybride"
    
    # Diesel
    if "DIESEL" in u or "TDI" in u or "CDI" in u or "DPE" in u or u.startswith("D"):
        return "Diesel"
    
    # Benzine (default)
    return "Benzine"

# 🧩 Pas de functie toe op je DataFrame
data["Type"] = data.apply(lambda row: bepaal_type(row["Merk"], row["Uitvoering"]), axis=1)


# --- CATEGORIEËN CONTROLEREN ---
# Verzekeren dat Type kolom Elektrisch/Hybride/Benzine/Diesel bevat
st.write("Beschikbare brandstofcategorieën:", data["Type"].unique())


# Zet om naar string en verwijder eventuele .0
data["Datum eerste toelating"] = data["Datum eerste toelating"].astype(str).str.split(".").str[0]

# Converteer naar datetime met format YYYYMMDD
data["Datum eerste toelating"] = pd.to_datetime(
    data["Datum eerste toelating"], format="%Y%m%d", errors="coerce"
)

# Eventuele lege of niet-parseerbare datums verwijderen
data = data.dropna(subset=["Datum eerste toelating"])

# **Filteren op datum > 2010**
data = data[data["Datum eerste toelating"].dt.year > 2010]

# Nu kun je Maand kolom maken
data["Maand"] = data["Datum eerste toelating"].dt.to_period("M").dt.to_timestamp()

# Tel aantal voertuigen per maand en brandstoftype
maand_aantal = data.groupby(["Maand", "Type"]).size().unstack(fill_value=0)

# --- CUMULATIEVE SOM BEREKENEN ---
cumulatief = maand_aantal.cumsum()

# --- LIJNDIAGRAM MET STREAMLIT ---
st.line_chart(cumulatief)

# --- EXTRA INFO ---
st.write("Data voorbeeld:", cumulatief.head())
