import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.statespace.varmax import VARMAX
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error
import warnings

warnings.filterwarnings("ignore")

# ==============================================================
# 📦 DATA INLADEN
# ==============================================================
@st.cache_data
def load_data():
    df_auto = pd.read_csv("duitse_automerken_JA.csv")
    return df_auto

df_auto = load_data()

st.title("📊 Voorspellend model voertuigregistraties")
st.markdown("---")
st.subheader("Voorspelling aantal voertuigen per brandstoftype in Nederland")

# ==============================================================
# ⚙️ INTERACTIEVE INSTELLINGEN
# ==============================================================
eindjaar = st.slider("Voorspellen tot jaar", 2025, 2050, 2030)
EINDDATUM = pd.Timestamp(f"{eindjaar}-12-01")
ev_groeifactor = st.slider("EV groeifactor (1 = historisch, >1 = versneld)", 1.0, 3.0, 1.5)
scenario = st.selectbox("Kies scenario voor voertuiggroei", ["Basis", "Optimistisch", "Pessimistisch"])
verbod_jaar = st.slider("Verbod op nieuwe Benzine/Diesel auto’s vanaf jaar", 2030, 2040, 2035)

# ==============================================================
# 🚗 TYPE BEPALEN
# ==============================================================
def bepaal_type(merk, uitvoering):
    m = str(merk).upper()
    u = str(uitvoering).upper()
    if "EV" in u or "BMW I" in m or "PORSCHE" in m:
        return "Elektrisch"
    if "DIESEL" in u or "TDI" in u or "CDI" in u or u.startswith("D"):
        return "Diesel"
    return "Benzine"

df_auto["Type"] = df_auto.apply(lambda r: bepaal_type(r.get("Merk",""), r.get("Uitvoering","")), axis=1)

# ==============================================================
# 🧹 DATUM OPSCHONEN
# ==============================================================
df_auto["Datum eerste toelating"] = pd.to_datetime(
    df_auto["Datum eerste toelating"].astype(str).str[:8],
    format="%Y%m%d",
    errors="coerce"
)

df_auto = df_auto.dropna(subset=["Datum eerste toelating"])
df_auto = df_auto[df_auto["Datum eerste toelating"].dt.year > 2010]
df_auto["Maand"] = df_auto["Datum eerste toelating"].dt.to_period("M").dt.to_timestamp()

maand_counts = df_auto.groupby(["Maand","Type"]).size().unstack(fill_value=0).sort_index()
if maand_counts.empty:
    st.error("⚠ Geen bruikbare data gevonden na 2010.")
    st.stop()

# ==============================================================
# 📈 HISTORISCH EN FORECAST INDEX
# ==============================================================
cumul_hist = maand_counts.cumsum()
laatste_maand = cumul_hist.index.max()
forecast_start = laatste_maand + pd.DateOffset(months=1)
forecast_index = pd.date_range(start=forecast_start, end=EINDDATUM, freq="MS")
h = len(forecast_index)
if h <= 0:
    st.error("⚠ Geen forecast-horizon (controleer eindjaar).")
    st.stop()

# ==============================================================
# 🔮 VARMAX MODEL
# ==============================================================
@st.cache_data
def fit_varmax(data):
    if len(data) >= 24:
        try:
            model = VARMAX(data.astype(float), order=(1,1))
            fit = model.fit(disp=False)
            return fit
        except:
            return None
    return None

varmax_fit = fit_varmax(maand_counts)
if varmax_fit:
    varmax_forecast = varmax_fit.forecast(steps=h)
else:
    varmax_forecast = pd.DataFrame(0, index=forecast_index, columns=maand_counts.columns)

# ==============================================================
# 🔮 SARIMAX MODEL
# ==============================================================
@st.cache_data
def fit_sarimax(y, exog, future_exog):
    if len(y) >= 24:
        try:
            model = SARIMAX(y, order=(1,1,1), seasonal_order=(1,1,0,12), exog=exog)
            fit = model.fit(disp=False)
            pred = fit.get_forecast(steps=len(future_exog), exog=future_exog)
            return pred.predicted_mean, pred.conf_int()
        except:
            pass
    # Fallback: lineaire trend
    x = np.arange(len(y))
    m, b = np.polyfit(x, y, 1)
    future_x = np.arange(len(y), len(y)+len(future_exog))
    return pd.Series(b + m*future_x, index=future_exog.index), None

exog = pd.DataFrame({"trend": np.arange(len(maand_counts))}, index=maand_counts.index)
future_exog = pd.DataFrame({"trend": np.arange(len(maand_counts), len(maand_counts)+h)}, index=forecast_index)

sarimax_forecasts, sarimax_cis = {}, {}
for col in maand_counts.columns:
    pred, ci = fit_sarimax(maand_counts[col], exog, future_exog)
    sarimax_forecasts[col] = pred
    sarimax_cis[col] = ci

sarimax_forecast = pd.DataFrame(sarimax_forecasts)

# ==============================================================
# ⚖️ ENSEMBLE WEIGHTS
# ==============================================================
weights = {}
for col in maand_counts.columns:
    rmse_varmax = rmse_sarimax = np.inf
    if varmax_fit is not None and col in varmax_fit.fittedvalues.columns:
        rmse_varmax = np.sqrt(mean_squared_error(maand_counts[col][-12:], varmax_fit.fittedvalues[col][-12:]))
    if col in sarimax_forecast.columns:
        rmse_sarimax = np.sqrt(mean_squared_error(maand_counts[col][-12:], sarimax_forecast[col][-12:]))
    total = rmse_varmax + rmse_sarimax + 1e-5
    weights[col] = {
        "varmax": 1 - rmse_varmax/total,
        "sarimax": 1 - rmse_sarimax/total
    }

# ==============================================================
# 🔗 COMBINEER FORECASTS
# ==============================================================
combined_forecast = pd.DataFrame(index=forecast_index, columns=maand_counts.columns)
for col in maand_counts.columns:
    w = weights[col]
    combined_forecast[col] = w["varmax"]*varmax_forecast[col] + w["sarimax"]*sarimax_forecast[col]
combined_forecast = combined_forecast.clip(lower=0)

# ==============================================================
# ⚡ SCENARIO’S & GROEIFACTOREN
# ==============================================================
groeifactoren = {"Elektrisch": ev_groeifactor, "Diesel": 1.0, "Benzine": 1.0}
if scenario == "Optimistisch":
    groeifactoren = {"Elektrisch": ev_groeifactor*1.2, "Diesel": 1.1, "Benzine": 0.9}
elif scenario == "Pessimistisch":
    groeifactoren = {"Elektrisch": ev_groeifactor*0.8, "Diesel": 0.9, "Benzine": 0.95}

for col in combined_forecast.columns:
    factor = groeifactoren.get(col, 1.0)
    combined_forecast[col] *= factor

# ==============================================================
# 🚫 VERBOD + OVERSCHUIVING NAAR EV
# ==============================================================
verbod_maanden = combined_forecast.index.year >= verbod_jaar
overschuif = combined_forecast.loc[verbod_maanden, ["Benzine","Diesel"]].sum(axis=1)
combined_forecast.loc[verbod_maanden, ["Benzine","Diesel"]] = 0
if "Elektrisch" in combined_forecast.columns:
    combined_forecast.loc[verbod_maanden, "Elektrisch"] += overschuif

# Pas CI aan
for col in maand_counts.columns:
    ci = sarimax_cis.get(col)
    if ci is not None:
        if col in ["Benzine","Diesel"]:
            ci.loc[verbod_maanden, :] = np.nan
        elif col == "Elektrisch":
            ci.iloc[:,0] += overschuif.values
            ci.iloc[:,1] += overschuif.values

# ==============================================================
# 📊 CUMULATIEVE FORECAST
# ==============================================================
forecast_cum = cumul_hist.iloc[-1] + combined_forecast.cumsum()

# ==============================================================
# 📉 PLOT
# ==============================================================
if maand_counts.empty or combined_forecast.empty:
    st.error("⚠ Geen data beschikbaar om te plotten.")
    st.stop()

alle_categorieen = maand_counts.columns.tolist()
categorieen = st.multiselect("Kies brandstoftypes om te tonen", options=alle_categorieen, default=alle_categorieen)
if not categorieen:
    categorieen = alle_categorieen

colors = {"Elektrisch": "green", "Diesel": "blue", "Benzine": "red"}
fig = go.Figure()

for col in categorieen:
    # Historisch
    fig.add_trace(go.Scatter(
        x=cumul_hist.index, y=cumul_hist[col],
        mode="lines", name=f"{col} (historisch)",
        line=dict(color=colors.get(col,"grey"), width=2)
    ))
    # Voorspelling
    fig.add_trace(go.Scatter(
        x=forecast_index, y=forecast_cum[col],
        mode="lines", name=f"{col} (voorspelling)",
        line=dict(color=colors.get(col,"grey"), dash="dash", width=3)
    ))
    # Confidence interval
    ci = sarimax_cis.get(col)
    if ci is not None and not ci.isna().all().all():
        fill_color = (
            "rgba(0,128,0,0.15)" if col=="Elektrisch" else
            "rgba(0,0,255,0.15)" if col=="Diesel" else
            "rgba(255,0,0,0.15)"
        )
        fig.add_trace(go.Scatter(
            x=list(forecast_index) + list(forecast_index[::-1]),
            y=list(ci.iloc[:,0]) + list(ci.iloc[:,1][::-1]),
            fill="toself",
            fillcolor=fill_color,
            line=dict(color="rgba(255,255,255,0)"),
            showlegend=False,
            name=f"{col} CI"
        ))

fig.update_layout(
    title=f"Voertuigregistraties per brandstoftype — Historisch + voorspelling tot {eindjaar}",
    xaxis_title="Jaar",
    yaxis_title="Aantal voertuigen (cumulatief)",
    hovermode="x unified",
    height=720,
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
)

st.plotly_chart(fig, use_container_width=True)
