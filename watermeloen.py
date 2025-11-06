pip install --user statsmodels

from statsmodels.tsa.statespace.varmax import VARMAX
from statsmodels.tsa.statespace.sarimax import SARIMAX
import numpy as np
import pandas as pd
# ------------------- Pagina 3 --------------------------
#elif page == "📊 Voorspellend model":
st.markdown("## Voorspellend Model")
st.markdown("---")
st.subheader("Voorspelling auto's in Nederland per brandstofcategorie")

warnings.filterwarnings("ignore")

# ---------- Interactieve instellingen ----------
eindjaar = st.slider("Voorspellen tot jaar", 2025, 2050, 2030)
EINDDATUM = pd.Timestamp(f"{eindjaar}-12-01")

# ---------- Kopie gebruiken ----------
df_auto_kopie = df_auto.copy()

# ---------- Type bepalen ----------
def bepaal_type(merk, uitvoering):
     u = str(uitvoering).upper()
     m = str(merk).upper()
     if ("BMW I" in m or "PORSCHE" in m or
        u.startswith(("FA1FA1CZ","3EER","3EDF","3EDE","2EER","2EDF","2EDE",
                      "E11","0AW5","QE2QE2G1","QE1QE1G1","HE1HE1G1")) or
        "EV" in u or "FA1FA1MD" in u):
         return "Elektrisch"
     if "DIESEL" in u or "TDI" in u or "CDI" in u or "DPE" in u or u.startswith("D"):
         return "Diesel"
     return "Benzine"

df_auto_kopie["Type"] = df_auto_kopie.apply(
    lambda r: bepaal_type(r.get("Merk",""), r.get("Uitvoering","")), axis=1
)

# ---------- Datums opschonen ----------
df_auto_kopie["Datum eerste toelating"] = df_auto_kopie["Datum eerste toelating"].astype(str).str.split(".").str[0]
df_auto_kopie["Datum eerste toelating"] = pd.to_datetime(
    df_auto_kopie["Datum eerste toelating"], format="%Y%m%d", errors="coerce"
)

# ---------- Filteren en groeperen ----------
df_auto_kopie2 = df_auto_kopie.dropna(subset=["Datum eerste toelating"])
df_auto_kopie2 = df_auto_kopie2[df_auto_kopie2["Datum eerste toelating"].dt.year > 2010]
df_auto_kopie2["Maand"] = df_auto_kopie2["Datum eerste toelating"].dt.to_period("M").dt.to_timestamp()

maand_counts_charging = df_auto_kopie2.groupby(["Maand", "Type"]).size().unstack(fill_value=0).sort_index()
if maand_counts_charging.empty:
    st.error("⚠ Geen bruikbare data gevonden in dataset na 2010.")
    st.stop()

    # ---------- Historische cumulatieven ----------


# ---------- Cumulatief historisch ----------
cumul_hist_charging = maand_counts_charging.cumsum()
laatste_hist_maand = cumul_hist_charging.index.max()
forecast_start = laatste_hist_maand + pd.DateOffset(months=1)

if forecast_start > EINDDATUM:
    st.error("⚠ Het gekozen eindjaar ligt vóór de laatste beschikbare data. Kies een later jaar.")
    st.stop()

forecast_index = pd.date_range(start=forecast_start, end=EINDDATUM, freq="MS")
h = len(forecast_index)
if h <= 0:
    st.error("⚠ Geen forecast-horizon (controleer eindjaar).")
    st.stop()

# =========================================================
#   1. Multivariate model (VARMAX)
# =========================================================
data = maand_counts_charging.astype(float)
if len(data) >= 24:
    try:
        varmax_model = VARMAX(data, order=(1,1))
        varmax_fit = varmax_model.fit(disp=False)
        varmax_forecast = varmax_fit.forecast(steps=h)
    except Exception as e:
        st.warning(f"VARMAX niet geslaagd: {e}")
        varmax_forecast = pd.DataFrame(0, index=forecast_index, columns=data.columns)
else:
    varmax_forecast = pd.DataFrame(0, index=forecast_index, columns=data.columns)

# =========================================================
#   2. SARIMAX met exogene variabelen
# =========================================================
# (Hier kun je echte externe variabelen inladen, bijv. prijzen of laadpunten)
exog = pd.DataFrame({
    "trend": np.arange(len(maand_counts_charging))
}, index=maand_counts_charging.index)
future_exog = pd.DataFrame({
    "trend": np.arange(len(maand_counts_charging), len(maand_counts_charging)+h)
}, index=forecast_index)

sarimax_forecasts = {}
for col in maand_counts_charging.columns:
    y = maand_counts_charging[col].astype(float)
    try:
        if len(y) >= 24:
            model = SARIMAX(y, order=(1,1,1), seasonal_order=(1,1,0,12), exog=exog)
            fit = model.fit(disp=False)
            pred = fit.get_forecast(steps=h, exog=future_exog).predicted_mean
            sarimax_forecasts[col] = pred
        else:
            # fallback naar lineair model
            x = np.arange(len(y))
            m, b = np.polyfit(x, y, 1)
            future_x = np.arange(len(y), len(y)+h)
            sarimax_forecasts[col] = pd.Series(b + m*future_x, index=forecast_index)
    except Exception as e:
        st.warning(f"SARIMAX mislukt voor {col}: {e}")
        # fallback lineair
        x = np.arange(len(y))
        m, b = np.polyfit(x, y, 1)
        future_x = np.arange(len(y), len(y)+h)
        sarimax_forecasts[col] = pd.Series(b + m*future_x, index=forecast_index)

sarimax_forecast = pd.DataFrame(sarimax_forecasts)

# =========================================================
#   3. Ensemble van VARMAX + SARIMAX
# =========================================================
# (Je kunt dit ook gewogen doen, bijvoorbeeld op basis van recente foutmarges)
combined_forecast = 0.5 * varmax_forecast + 0.5 * sarimax_forecast
combined_forecast = combined_forecast.clip(lower=0)

# =========================================================
#   4. Maak cumulatief
# =========================================================
forecast_cum = cumul_hist_charging.iloc[-1] + combined_forecast.cumsum()
forecast_median_charging = forecast_cum.copy()

# =========================================================
#   5. Selectie + Plotly visualisatie
# =========================================================
categorieen = st.multiselect(
    "Kies brandstoftypes om te tonen",
    options=maand_counts_charging.columns.tolist(),
    default=maand_counts_charging.columns.tolist()
)

fig = go.Figure()
for col in categorieen:
    # Historische lijnen
    fig.add_trace(go.Scatter(
        x=cumul_hist_charging.index,
        y=cumul_hist_charging[col],
        mode="lines",
        name=f"{col} (historisch)",
        line=dict(width=2)
    ))
    # Voorspelling
    fig.add_trace(go.Scatter(
        x=forecast_index,
        y=forecast_median_charging[col].astype(float),
        mode="lines",
        line=dict(dash="dash", width=3),
        name=f"{col} (voorspelling)"
    ))

fig.update_layout(
    title=f"Voertuigregistraties per brandstoftype — Historisch + gecombineerde voorspelling tot {eindjaar}",
    xaxis_title="Jaar",
    yaxis_title="Aantal voertuigen (cumulatief)",
    hovermode="x unified",
    height=720
)

st.plotly_chart(fig, use_container_width=True)
