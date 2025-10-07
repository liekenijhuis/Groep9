import pandas as pd
import pickle

data = pd.read_csv("duitse_automerken.csv")

# --- Definieer herkenningspatronen per type ---
def bepaal_type(merk, uitvoering):
    u = str(uitvoering).upper()
    m = str(merk).upper()

    # Elektrisch
    if "BMW I" in m or "TESLA" in m or u.startswith("E11") or "EV" in u:
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

# 🧹 Houd alleen de gewenste kolommen
resultaat = data[["Merk", "Uitvoering", "Type", "Datum eerste toelating"]].drop_duplicates().reset_index(drop=True)

# 💾 Sla op als CSV-bestand
resultaat.to_csv("auto_types.csv", index=False)

print("✅ Bestand 'auto_types.csv' is aangemaakt!")
print(resultaat.head())