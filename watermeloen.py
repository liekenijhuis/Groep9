# ------------------- 📊 VOORSPELLEND MODEL --------------------------
st.markdown("## Voorspellend Model")
st.markdown("---")
st.subheader("Voorspelling auto's in Nederland per brandstofcategorie")

warnings.filterwarnings("ignore")

# ---------- Interactieve instellingen ----------
eindjaar = st.slider("Voorspellen tot jaar", 2025, 2050, 2030)
EINDDATUM = pd.Timestamp(f"{eindjaar}-12-01")

# ---------- EV groeifactor slider ----------
ev_groeifactor = st.slider("EV-groeifactor", 1.0, 3.0, 1.5, 0.1)

# ---------- Scenario-keuze ----------
scenario = st.selectbox(
    "Kies scenario voor voertuiggroei",
    options=["Basis", "Optimistisch", "Pessimistisch"]
)

# ---------- Verbodsjaar ----------
verbod_jaar = st.slider("Verbod op nieuwe Benzine/Diesel auto’s vanaf jaar", 2030, 2040, 2035)

# ---------- Dataset voorbereiden ----------
df_auto_kopie = df_auto.copy()

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

df_auto_kopie["Datum eerste toelating"] = pd.to_datetime(
    df_auto_kopie["Datum eerste toelating"].astype(str).str.split(".").str[0],
    format="%Y%m%d", errors="coerce"
)
df_auto_kopie = df_auto_kopie.dropna(subset=["Datum eerste toelating"])
df_auto_kopie = df_auto_kopie[df_auto_kopie["Datum eerste toelating"].dt.year > 2010]
df_auto_kopie["Maand"] = df_auto_kopie["Datum eerste toelating"].dt.to_period("M").dt.to_timestamp()

maand_counts = df_auto_kopie.groupby(["Maand","Type"]).size().unstack(fill_value=0).sort_index()
if maand_counts.empty:
    st.error("⚠ Geen bruikbare data gevonden in dataset na 2010.")
    st.stop()

# ---------- Forecast-instellingen ----------
cumul_hist = maand_counts.cumsum()
laatste_hist_maand = cumul_hist.index.max()
forecast_start = laatste_hist_maand + pd.DateOffset(months=1)
forecast_index = pd.date_range(start=forecast_start, end=EINDDATUM, freq="MS")
h = len(forecast_index)
if h <= 0:
    st.error("⚠ Geen forecast-horizon (controleer eindjaar).")
    st.stop()

# =========================================================
#   1. VARMAX
# =========================================================
data = maand_counts.astype(float)
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
#   2. SARIMAX
# =========================================================
exog = pd.DataFrame({"trend": np.arange(len(data))}, index=data.index)
future_exog = pd.DataFrame({"trend": np.arange(len(data), len(data)+h)}, index=forecast_index)
sarimax_forecasts, sarimax_cis = {}, {}

for col in data.columns:
    y = data[col].astype(float)
    try:
        if len(y) >= 24:
            model = SARIMAX(y, order=(1,1,1), seasonal_order=(1,1,0,12), exog=exog)
            fit = model.fit(disp=False)
            pred = fit.get_forecast(steps=h, exog=future_exog)
            sarimax_forecasts[col] = pred.predicted_mean
            sarimax_cis[col] = pred.conf_int(alpha=0.2)  # CI 80%
        else:
            x = np.arange(len(y))
            m, b = np.polyfit(x, y, 1)
            future_x = np.arange(len(y), len(y)+h)
            sarimax_forecasts[col] = pd.Series(b + m*future_x, index=forecast_index)
    except Exception as e:
        st.warning(f"SARIMAX mislukt voor {col}: {e}")
        x = np.arange(len(y))
        m, b = np.polyfit(x, y, 1)
        future_x = np.arange(len(y), len(y)+h)
        sarimax_forecasts[col] = pd.Series(b + m*future_x, index=forecast_index)

sarimax_forecast = pd.DataFrame(sarimax_forecasts)

# =========================================================
#   3. Ensemble
# =========================================================
combined_forecast = 0.5 * varmax_forecast + 0.5 * sarimax_forecast
combined_forecast = combined_forecast.clip(lower=0)

# =========================================================
#   4. Scenario & groeifactoren
# =========================================================
groeifactoren = {"Elektrisch": ev_groeifactor, "Diesel": 1.0, "Benzine": 1.0}
if scenario == "Optimistisch":
    groeifactoren = {"Elektrisch": ev_groeifactor*1.2, "Diesel": 1.1, "Benzine": 0.9}
elif scenario == "Pessimistisch":
    groeifactoren = {"Elektrisch": ev_groeifactor*0.8, "Diesel": 0.9, "Benzine": 0.95}

for col in combined_forecast.columns:
    factor = groeifactoren.get(col, 1.0)
    combined_forecast[col] *= factor

# =========================================================
#   5. Verbod op Benzine/Diesel vanaf 2035
# =========================================================
for col in ["Benzine", "Diesel"]:
    if col in combined_forecast.columns:
        combined_forecast.loc[combined_forecast.index.year >= verbod_jaar, col] = 0

# =========================================================
#   6. Cumulatief maken
# =========================================================
forecast_cum = cumul_hist.iloc[-1] + combined_forecast.cumsum()

# =========================================================
#   7. Plotly Visualisatie
# =========================================================
categorieen = st.multiselect(
    "Kies brandstoftypes om te tonen",
    options=maand_counts.columns.tolist(),
    default=maand_counts.columns.tolist()
)

fig = go.Figure()
for col in categorieen:
    # Historische lijnen
    fig.add_trace(go.Scatter(
        x=cumul_hist.index, y=cumul_hist[col],
        mode="lines", name=f"{col} (historisch)",
        line=dict(width=2)
    ))

    # Voorspelling
    fig.add_trace(go.Scatter(
        x=forecast_index, y=forecast_cum[col],
        mode="lines", name=f"{col} (voorspelling)",
        line=dict(width=3, dash="dash")
    ))

    # Confidence Interval (smal, meebewegend)
    ci = sarimax_cis.get(col)
    if ci is not None:
        ci_lower = forecast_cum[col] - combined_forecast[col] + ci.iloc[:,0]
        ci_upper = forecast_cum[col] - combined_forecast[col] + ci.iloc[:,1]
        fill_color = (
            "rgba(0,128,0,0.15)" if col=="Elektrisch"
            else "rgba(0,0,255,0.15)" if col=="Diesel"
            else "rgba(255,0,0,0.15)"
        )
        fig.add_trace(go.Scatter(
            x=list(forecast_index) + list(forecast_index[::-1]),
            y=list(ci_lower) + list(ci_upper[::-1]),
            fill='toself', fillcolor=fill_color,
            line=dict(color='rgba(255,255,255,0)'),
            showlegend=False, name=f"{col} CI"
        ))

fig.update_layout(
    title=f"Voertuigregistraties per brandstoftype — Historisch + voorspelling tot {eindjaar}",
    xaxis_title="Jaar",
    yaxis_title="Aantal voertuigen (cumulatief)",
    hovermode="x unified",
    height=720
)
st.plotly_chart(fig, use_container_width=True)
