import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.statespace.varmax import VARMAX
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error
import warnings

warnings.filterwarnings("ignore")

# ------------------- Data inladen -----------------------
@st.cache_data
def load_data():
    df_auto = pd.read_csv("duitse_automerken_JA.csv")
    return df_auto

df_auto = load_data()

# ------------------- Pagina --------------------------
st.markdown("## Voorspellend Model")
st.markdown("---")
st.subheader("Voorspelling auto's in Nederland per brandstofcategorie")

# ---------- Interactieve instellingen ----------
eindjaar = st.slider("Voorspellen tot jaar", 2025, 2050, 2030)
EINDDATUM = pd.Timestamp(f"{eindjaar}-12-01")

# ---------- EV groeifactor slider ----------
ev_groeifactor = st.slider("EV groeifactor (1 = historisch, >1 = versneld)", 1.0, 3.0, 1.5)

# ---------- Type bepalen ----------
TYPE_PATTERNS = {
    "Elektrisch": ["BMW I", "PORSCHE", "EV", "FA1FA1MD"],
    "Diesel": ["DIESEL", "TDI", "CDI", "DPE"]
}

def bepaal_type(merk, uitvoering):
    m = str(merk).upper()
    u = str(uitvoering).upper()
    for t, patterns in TYPE_PATTERNS.items():
        if any(p in m for p in patterns) or any(u.startswith(p) for p in patterns):
            return t
    return "Benzine"

df_auto["Type"] = df_auto.apply(
    lambda r: bepaal_type(r.get("Merk", ""), r.get("Uitvoering", "")), axis=1
)

# ---------- Datum opschonen ----------
df_auto["Datum eerste toelating"] = pd.to_datetime(
    df_auto["Datum eerste toelating"].astype(str).str[:8],
    format="%Y%m%d",
    errors="coerce"
)
df_auto2 = df_auto.dropna(subset=["Datum eerste toelating"])
df_auto2 = df_auto2[df_auto2["Datum eerste toelating"].dt.year > 2010]
df_auto2["Maand"] = df_auto2["Datum eerste toelating"].dt.to_period("M").dt.to_timestamp()

maand_counts = df_auto2.groupby(["Maand", "Type"]).size().unstack(fill_value=0).sort_index()
if maand_counts.empty:
    st.error("⚠ Geen bruikbare data gevonden na 2010.")
    st.stop()

# ---------- Historische cumulatieven ----------
cumul_hist = maand_counts.cumsum()
laatste_maand = cumul_hist.index.max()
forecast_start = laatste_maand + pd.DateOffset(months=1)

if forecast_start > EINDDATUM:
    st.error("⚠ Het gekozen eindjaar ligt vóór de laatste beschikbare data.")
    st.stop()

forecast_index = pd.date_range(start=forecast_start, end=EINDDATUM, freq="MS")
h = len(forecast_index)
if h <= 0:
    st.error("⚠ Geen forecast-horizon.")
    st.stop()

# ================= VARMAX MODEL =================
@st.cache_data
def fit_varmax(data):
    if len(data) >= 24:
        try:
            model = VARMAX(data.astype(float), order=(1, 1))
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

# ================= SARIMAX MODEL =================
@st.cache_data
def fit_sarimax(y, exog, future_exog):
    if len(y) >= 24:
        try:
            model = SARIMAX(y.astype(float), order=(1, 1, 1),
                            seasonal_order=(1, 1, 0, 12), exog=exog)
            fit = model.fit(disp=False)
            pred_mean = fit.get_forecast(steps=len(future_exog), exog=future_exog).predicted_mean
            pred_ci = fit.get_forecast(steps=len(future_exog), exog=future_exog).conf_int()
            return pred_mean, pred_ci
        except:
            # fallback lineair
            x = np.arange(len(y))
            m, b = np.polyfit(x, y, 1)
            future_x = np.arange(len(y), len(y) + len(future_exog))
            pred_series = pd.Series(b + m * future_x, index=future_exog.index)
            return pred_series, None
    else:
        x = np.arange(len(y))
        m, b = np.polyfit(x, y, 1)
        future_x = np.arange(len(y), len(y) + len(future_exog))
        pred_series = pd.Series(b + m * future_x, index=future_exog.index)
        return pred_series, None

exog = pd.DataFrame({"trend": np.arange(len(maand_counts))}, index=maand_counts.index)
future_exog = pd.DataFrame({"trend": np.arange(len(maand_counts), len(maand_counts) + h)},
                           index=forecast_index)

sarimax_forecasts = {}
sarimax_cis = {}
for col in maand_counts.columns:
    pred, ci = fit_sarimax(maand_counts[col], exog, future_exog)
    sarimax_forecasts[col] = pred
    sarimax_cis[col] = ci

sarimax_forecast = pd.DataFrame(sarimax_forecasts)

# ================= ENSEMBLE =================
weights = {}
for col in maand_counts.columns:
    rmse_varmax = np.sqrt(mean_squared_error(maand_counts[col][-12:], varmax_fit.fittedvalues[col][-12:])) if varmax_fit else np.inf
    rmse_sarimax = np.sqrt(mean_squared_error(maand_counts[col][-12:], sarimax_forecast[col][-12:])) if len(maand_counts) >= 12 else 1
    total = rmse_varmax + rmse_sarimax
    weights[col] = {
        "varmax": (1 - rmse_varmax / (total + 1e-5)),
        "sarimax": (1 - rmse_sarimax / (total + 1e-5))
    }

combined_forecast = pd.DataFrame(index=forecast_index, columns=maand_counts.columns)
for col in maand_counts.columns:
    w = weights[col]
    combined_forecast[col] = w["varmax"] * varmax_forecast[col] + w["sarimax"] * sarimax_forecast[col]

combined_forecast = combined_forecast.clip(lower=0)

# ================= SCENARIO GROEIFACTOREN =================
scenario = st.selectbox(
    "Kies scenario voor voertuiggroei",
    options=["Basis", "Optimistisch", "Pessimistisch"]
)

groeifactoren = {"Elektrisch": ev_groeifactor, "Diesel": 1.0, "Benzine": 1.0}

if scenario == "Optimistisch":
    groeifactoren = {"Elektrisch": ev_groeifactor * 1.2, "Diesel": 1.1, "Benzine": 0.9}
elif scenario == "Pessimistisch":
    groeifactoren = {"Elektrisch": ev_groeifactor * 0.8, "Diesel": 0.9, "Benzine": 0.95}

for col in combined_forecast.columns:
    factor = groeifactoren.get(col, 1.0)
    combined_forecast[col] *= factor

# ================= Geen verdere groei na 2035 =================
verbod_jaar = 2035
for col in ["Benzine", "Diesel", "Elektrisch"]:
    if col in combined_forecast.columns:
        # Houd waarde constant vanaf 2035
        laatste_waarde = forecast_cum.loc[forecast_cum.index.year == verbod_jaar - 1, col].iloc[-1]
        combined_forecast.loc[combined_forecast.index.year >= verbod_jaar, col] = 0
        forecast_cum.loc[forecast_cum.index.year >= verbod_jaar, col] = laatste_waarde


# ================= CUMULATIEF =================
forecast_cum = cumul_hist.iloc[-1] + combined_forecast.cumsum()

# ================= PLOT =================
categorieen = st.multiselect(
    "Kies brandstoftypes om te tonen",
    options=maand_counts.columns.tolist(),
    default=maand_counts.columns.tolist()
)

colors = {"Elektrisch": "green", "Diesel": "blue", "Benzine": "red"}

fig = go.Figure()
for col in categorieen:
    # Historisch
    fig.add_trace(go.Scatter(
        x=cumul_hist.index, y=cumul_hist[col],
        mode="lines", name=f"{col} (historisch)",
        line=dict(color=colors.get(col, "grey"), width=2)
    ))
    # Voorspelling
    fig.add_trace(go.Scatter(
        x=forecast_index, y=forecast_cum[col],
        mode="lines", name=f"{col} (voorspelling)",
        line=dict(color=colors.get(col, "grey"), dash="dash", width=3)
    ))
    # Confidence interval
    ci = sarimax_cis.get(col)
    if ci is not None:
        last_hist = cumul_hist.iloc[-1][col]
        ci_lower = forecast_cum[col] - combined_forecast[col] + ci.iloc[:, 0]
        ci_upper = forecast_cum[col] - combined_forecast[col] + ci.iloc[:, 1]

        fill_color = (
            "rgba(0,128,0,0.2)" if col == "Elektrisch"
            else "rgba(0,0,255,0.2)" if col == "Diesel"
            else "rgba(255,0,0,0.2)"
        )

        fig.add_trace(go.Scatter(
            x=list(forecast_index) + list(forecast_index[::-1]),
            y=list(ci_lower) + list(ci_upper[::-1]),
            fill='toself',
            fillcolor=fill_color,
            line=dict(color='rgba(255,255,255,0)'),
            showlegend=False,
            name=f"{col} CI"
        ))

fig.update_layout(
    title=f"Voertuigregistraties per brandstoftype — Historisch + gecombineerde voorspelling tot {eindjaar}",
    xaxis_title="Jaar",
    yaxis_title="Aantal voertuigen (cumulatief)",
    hovermode="x unified",
    height=720
)

st.plotly_chart(fig, use_container_width=True)
