#-------------------imports-----------------------------
#-------------------------------------------------------
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.cm as cm
import altair as alt

#-------------------data inladen-----------------------
#-------------------------------------------------------
#Main data set
@st.cache_data
def load_data():
    df = pd.read_csv("airline_passenger_satisfaction.csv")
    df["Total Delay"] = df["Departure Delay"].fillna(0) + df["Arrival Delay"].fillna(0)
    return df

df = load_data()

#Extra data set
@st.cache_data
def load_extra_data():
    df_extra = pd.read_csv("Surveydata_test_(1).csv")
    return df_extra

df_extra = load_extra_data()

#Aangepast train data set
@st.cache_data
def load_extra_data_aangepast():
    df_extra_aangepast = pd.read_csv("Train_Japan_Opgeschoond1.csv", delimiter=";")
    for col in df.select_dtypes(include=["int64", "float64"]).columns:
        df[col] = df[col].fillna(df[col].median())
    return df_extra_aangepast

df_extra_aangepast = load_extra_data_aangepast()

#-------------------sidebar-----------------------------
#-------------------------------------------------------
# Zorg dat er altijd een default waarde is
if "stijl" not in st.session_state:
    st.session_state["stijl"] = "KLM Blauw"

with st.sidebar:
    # Huidige stijl bepalen
    huidige_stijl = st.session_state["stijl"]
    primary_color = "royalblue" if huidige_stijl == "KLM Blauw" else "goldenrod"

    # Titel bovenaan
    st.markdown(
        f"<h2 style='color:{primary_color}; margin: 0 0 8px 0;'>KLM Dashboard</h2>",
        unsafe_allow_html=True,
    )

    # Radio button onder de titel
    st.radio("Kies een stijl:", ["KLM Blauw", "Geel"], key="stijl")

    st.markdown("---")

    # overige sidebar-elementen
    page = st.selectbox("Selecteer een pagina", ["Snel Overzicht", "Dashboard","Vliegtuig vs Trein", "Data Overzicht", "Werkwijze"])

    # witregel
    st.write("")  

    # Afbeelding
    st.image("Vertrekbord Team HV0009.png", use_container_width=True)

    # witregels
    st.write("") 
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")

    # Voeg laatst geupdate datum toe
    st.write("Voor het laatst geupdate op:")
    st.write("*15:56 - 25 sep 2025*")

#-------------------stijlinstellingen-------------------
#-------------------------------------------------------
stijl = st.session_state["stijl"]  # veilige kopie uit session_state

if stijl == "KLM Blauw":
    primary_color = "royalblue"
    secondary_color = "orange"
    gauge_steps = [
        {'range': [0,2], 'color': 'lightcoral'},
        {'range': [2,4], 'color': 'lightyellow'},
        {'range': [4,5], 'color': 'lightgreen'}
    ]
else:  # Geel
    primary_color = "goldenrod"
    secondary_color = "darkorange"
    gauge_steps = [
        {'range': [0,2], 'color': 'orangered'},
        {'range': [2,4], 'color': 'gold'},
        {'range': [4,5], 'color': 'lightyellow'}
    ]

#-------------------page 1-----------------------------
#-------------------------------------------------------
if page == "Snel Overzicht":

    # Titel in thema-kleur
    st.markdown(f"<h1 style='color:{primary_color}'>📊 Snel Overzicht - Klanttevredenheid KLM</h1>", unsafe_allow_html=True)
    st.write("")
    st.markdown("**Welkom!**")
    st.write("Op dit dashboard vind je uitgebreide informatie over de tevredenheid van klanten van KLM.")
    st.write("Gebruik het dropdown menu om de verschillende pagina's te bezoeken.")
    st.write("")
    st.markdown("**Snel overzicht**")
    st.write("Hieronder zijn een aantal simpele KPI's (Key Performance Indicators) te zien.")
    st.write("Klik op de afbeeldingen om ze beter te bekijken.")

    # ======================
    # Dropdown filter: Class
    # ======================
    st.markdown("### Selecteer een klasse")
    class_options = ["Alle Klassen"] + df["Class"].unique().tolist()
    selected_class = st.selectbox("Kies een klasse:", class_options)

    # Pas filter toe op df_filtered
    if selected_class != "Alle Klassen":
        df_filtered = df[df["Class"] == selected_class]
    else:
        df_filtered = df.copy()

    # ======================
    # Extra filtersectie - Afhankelijke sliders
    # ======================
    st.markdown("###  Leeftijdsfilter")
    st.write("Pas hier de minimale en maximale leeftijd aan.")
    st.write("Let op! Zorg dat de maximale leeftijd niet kleiner is dan de minimale leeftijd!")

    col_min, col_max = st.columns(2)
    with col_min:
        min_age = st.slider(
            "Minimum leeftijd",
            int(df_filtered["Age"].min()),
            int(df_filtered["Age"].max()),
            int(df_filtered["Age"].min()),
            key="min_age_slider"
        )
    with col_max:
        max_age = st.slider(
            "Maximum leeftijd",
            int(df_filtered["Age"].min()),
            int(df_filtered["Age"].max()),
            int(df_filtered["Age"].max()),
            key="max_age_slider"
        )

    if min_age > max_age:
        st.warning("⚠️ Minimum leeftijd kan niet groter zijn dan maximum. Waarden zijn aangepast.")
        min_age, max_age = max_age, min_age

    df_filtered = df_filtered[(df_filtered["Age"] >= min_age) & (df_filtered["Age"] <= max_age)]

    # ======================
    # KPI berekeningen
    # ======================
    total_passengers = df_filtered["ID"].nunique()
    satisfaction_cols = [
        "On-board Service", "Seat Comfort", "Leg Room Service", "Cleanliness",
        "Food and Drink", "In-flight Service", "In-flight Wifi Service",
        "In-flight Entertainment", "Baggage Handling"
    ]
    avg_satisfaction = df_filtered[satisfaction_cols].mean().mean()
    avg_dep_delay = df_filtered["Departure Delay"].mean()
    avg_arr_delay = df_filtered["Arrival Delay"].mean()
    delayed_percentage = (df_filtered[df_filtered["Total Delay"] > 15].shape[0] / len(df_filtered)) * 100 if len(df_filtered) > 0 else 0

    # ======================
    # Visualisaties (2x3 grid)
    # ======================
    col1, col2, col5 = st.columns(3)

    with col1:
        fig1 = go.Figure(go.Indicator(
            mode="number",
            value=total_passengers,
            title={"text": "Totaal Passagiers"},
            number={'font': {'color': primary_color}}
        ))
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_satisfaction,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Gem. Tevredenheid (0-5)"},
            gauge={
                'axis': {'range': [0, 5]},
                'bar': {'color': primary_color},
                'steps': gauge_steps
            }
        ))
        st.plotly_chart(fig2, use_container_width=True)

    with col5:
        fig5 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=delayed_percentage,
            title={'text': "Vertraagde vluchten (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': secondary_color},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 60], 'color': "lightyellow"},
                    {'range': [60, 100], 'color': "lightcoral"}
                ]
            },
            number={'suffix': "%"}
        ))
        st.plotly_chart(fig5, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        fig3 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_dep_delay,
            title={'text': "Gem. Vertrekvertraging (min)"},
            gauge={'axis': {'range': [0, max(60, avg_dep_delay*2)]}, 'bar': {'color': secondary_color}}
        ))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_arr_delay,
            title={'text': "Gem. Aankomstvertraging (min)"},
            gauge={'axis': {'range': [0, max(60, avg_arr_delay*2)]}, 'bar': {'color': "red"}}
        ))
        st.plotly_chart(fig4, use_container_width=True)

#-------------------page 2-----------------------------
#-------------------------------------------------------
elif page == "Dashboard":
    st.markdown(f"<h1 style='color:{primary_color}'>📊 Dashboard klanttevredenheid KLM</h1>", unsafe_allow_html=True)
    # Witregel
    st.write("")

    # Titel
    st.title("Tevredenheid per klanttype en reisdoel")
    #-------------------Grafiek Chris-------------------------
    #---------------------------------------------------------
    st.markdown("### ✈️ Vertragingfilters")
    delay_30 = st.checkbox("Alleen vertraagde vluchten (>30 minuten vertraging)")
    delay_60 = st.checkbox("Alleen zwaar vertraagde vluchten (>60 minuten vertraging)")

    df_filtered = df.copy()
    if delay_30 and delay_60:
        st.warning("⚠️ Beide filters geselecteerd. De strengste filter (>60 minuten) is toegepast.")
        df_filtered = df_filtered[df_filtered["Total Delay"] > 60]
    elif delay_30:
        df_filtered = df_filtered[df_filtered["Total Delay"] > 30]
    elif delay_60:
        df_filtered = df_filtered[df_filtered["Total Delay"] > 60]
    else:
        st.info("ℹ️ Geen filter geselecteerd. Alle vluchten worden getoond.")

    agg = df_filtered.groupby(["Customer Type", "Type of Travel", "Satisfaction"]).size().reset_index(name="count")
    agg["Group"] = agg["Customer Type"] + " - " + agg["Type of Travel"]

    fig = px.bar(
        agg,
        x="Group",
        y="count",
        color="Satisfaction",
        barmode="group",
        text_auto=True,
        color_discrete_sequence=[primary_color, "lightcoral"]
    )
    fig.update_layout(
        xaxis_title="Customer Type & Type of Travel",
        yaxis_title="Aantal passagiers",
        legend_title="Satisfaction"
    )

    # Afwisselend blauw/geel voor de x-as labels
    groups = agg["Group"].unique().tolist()
    colors = ["royalblue", "goldenrod"]  # wisselkleur
    tickvals = list(range(len(groups)))
    ticktext = [
        f"<span style='color:{colors[i % 2]}'>{grp}</span>"
        for i, grp in enumerate(groups)
    ]

    fig.update_xaxes(
        tickvals=tickvals,
        ticktext=ticktext
    )

    st.plotly_chart(fig, use_container_width=True)

    #-------------------Grafiek Koen---------------------------
    #---------------------------------------------------------
    # Titel
    st.title("Tevredenheid per categorie")

    # Dropdown voor Class-selectie (met "Alle Klassen")
    class_options = ["Alle Klassen"] + sorted(df["Class"].dropna().unique())
    selected_class = st.selectbox("Kies een klasse:", class_options)

    # Start met hele dataset of filter op gekozen klasse
    if selected_class == "Alle Klassen":
      filtered_df = df.copy()
    else:
        filtered_df = df[df["Class"] == selected_class]

    # Filter voor vertraagde vluchten (fallback op Total Delay > 15 als 'Flight Status' niet bestaat)
    delay_filter = st.checkbox("Toon alleen vertraagde vluchten ✈️", value=False)
    if delay_filter:
        if "Flight Status" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Flight Status"] == "Delayed"]
        elif "Total Delay" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["Total Delay"] > 15]
        else:
            st.warning("Geen 'Flight Status' of 'Total Delay' kolom gevonden; vertraagde filter niet toegepast.")

    # Verwachte aspecten (labels)
    expected_aspects = [
    "Ease of Online booking", "Checkin service", "Online boarding",
    "Gate location", "On-board service", "Seat comfort",
    "Leg room service", "Cleanliness", "Food and drink",
    "Inflight service", "Inflight wifi service", "Inflight entertainment",
    "Baggage handling"
    ]

    # Normaliseer kolomnamen voor robuuste matching
    import re
    def normalize(s: str) -> str:
        return re.sub(r'[^a-z0-9]', '', str(s).lower())

    norm_to_col = {normalize(col): col for col in df.columns}
    available_aspects = [(asp, norm_to_col[normalize(asp)]) for asp in expected_aspects if normalize(asp) in norm_to_col]

    # UI: multiselect voor aspecten
    labels = [label for label, _ in available_aspects]
    cols_map = {label: col for label, col in available_aspects}

    if not labels:
        st.warning("Geen satisfaction-aspecten gevonden in de dataset. Controleer kolomnamen.")
    else:
        st.write("Kies de aspecten die je wilt zien:")
        selected_labels = st.multiselect("Aspects", options=labels, default=labels)

        selected_cols = [cols_map[label] for label in selected_labels]

        # Alleen numerieke kolommen meenemen
        valid_cols = [c for c in selected_cols if c in filtered_df.columns and pd.api.types.is_numeric_dtype(filtered_df[c])]

        if valid_cols and len(filtered_df) > 0:
            mean_values = filtered_df[valid_cols].mean()
            # Zet index terug naar de gebruiksvriendelijke labels
            idx_to_label = {col: label for label, col in available_aspects}
            mean_values.index = [idx_to_label.get(col, col) for col in mean_values.index]
            st.bar_chart(mean_values)
        else:
            st.warning("Geen geldige numerieke aspecten geselecteerd, of er is geen data na filtering.")
    #-------------------Grafiek Ann---------------------------
    #---------------------------------------------------------
    # Title
    st.title("Gemiddelde tevredenheid per Geslacht en Klasse")

    # Kolommen met losse tevredenheidsaspecten
    satisfaction_cols = [
        "On-board Service", "Seat Comfort", "Leg Room Service", "Cleanliness",
        "Food and Drink", "In-flight Service", "In-flight Wifi Service",
        "In-flight Entertainment", "Baggage Handling"
    ]

    # Voeg kolom toe met gemiddelde tevredenheid per passagier
    df["Satisfaction_Avg"] = df[satisfaction_cols].mean(axis=1)

    # Filteropties
    gender_options = ["Alle Geslachten"] + df["Gender"].dropna().unique().tolist()
    selected_gender = st.selectbox("Kies een geslacht:", gender_options, key="gender_boxplot")

    class_options = ["Alle Klassen"] + df["Class"].dropna().unique().tolist()
    selected_class = st.selectbox("Kies een klasse:", class_options, key="class_boxplot")

    # Maak een filterkopie
    df_box = df.copy()

    if selected_gender != "Alle Geslachten":
        df_box = df_box[df_box["Gender"] == selected_gender]

    if selected_class != "Alle Klassen":
        df_box = df_box[df_box["Class"] == selected_class]

    # Alleen boxplot tekenen als er data is
    if df_box.empty:
        st.warning("Geen data beschikbaar voor deze selectie.")
    else:
        fig_box = px.box(
            df_box,
            x="Class",
            y="Satisfaction_Avg",
            color="Gender",
            color_discrete_map={
                "Male": primary_color,
                "Female": "lightcoral" if stijl == "KLM Blauw" else "goldenrod"
            }
        )
        fig_box.update_layout(
            xaxis_title="Klasse",
            yaxis_title="Gemiddelde tevredenheid (0-5)",
            yaxis=dict(range=[0, 5])  # schaal altijd 0–5
        )
        st.plotly_chart(fig_box, use_container_width=True)
    #-------------------Grafiek Lieke-------------------------
    #---------------------------------------------------------
    # Titel
    st.title("Tevredenheid en vertraging")

    # ======================
    # Rating maar één keer berekenen (beter in load_data())
    # ======================
    if "rating" not in df.columns:
        rating_cols = [
            "Ease of Online Booking","Check-in Service","Online Boarding","Gate Location",
            "On-board Service","Seat Comfort","Leg Room Service","Cleanliness",
            "Food and Drink","In-flight Service","In-flight Wifi Service",
            "In-flight Entertainment","Baggage Handling"
        ]
        df["rating"] = df[rating_cols].mean(axis=1)

    # --- Leeftijdsfilter ---
    st.markdown("### Leeftijdsfilter")
    age_range = st.slider(
        "Leeftijdsbereik",
        int(df["Age"].min()),
        int(df["Age"].max()),
        (int(df["Age"].min()), int(df["Age"].max())),
        key="age_range_slider"
    )
    min_age, max_age = age_range

    # --- Afstandsfilter ---
    st.markdown("### Vlucht Afstand Filter")
    distance_range = st.slider(
        "Afstandsbereik (Flight Distance)",
        int(df["Flight Distance"].min()),
        int(df["Flight Distance"].max()),
        (int(df["Flight Distance"].min()), int(df["Flight Distance"].max())),
        key="distance_range_slider"
    )
    min_dist, max_dist = distance_range

    # ======================
    # Data filteren
    # ======================
    filtered = df[
        (df["Age"] >= min_age) & (df["Age"] <= max_age) &
        (df["Flight Distance"] >= min_dist) & (df["Flight Distance"] <= max_dist)
    ]

    # ======================
    # Sampling toepassen bij grote datasets
    # ======================
    max_points = 10000
    if len(filtered) > max_points:
        filtered = filtered.sample(max_points, random_state=42)

    # ======================
    # Scatterplot met Altair (rating 0 = rood, 5 = groen)
    # ======================
    scatter = (
        alt.Chart(filtered)
        .mark_circle(opacity=0.4)
        .encode(
            x=alt.X("Arrival Delay", title="Arrival Delay (minuten)"),
            y=alt.Y("Departure Delay", title="Departure Delay (minuten)"),
            color=alt.Color(
                "rating",
                scale=alt.Scale(domain=[0, 5], range=["red", "orange", "green"]),
                title="Average Rating"
            ),
            tooltip=["Age", "Flight Distance", "Arrival Delay", "Departure Delay", "rating"]
        )
        .properties(
            title="Scatterplot van Arrival vs Departure Delay, gekleurd op Rating",
            width=700,
            height=500
        )
    )

    # Plot tonen in Streamlit
    st.altair_chart(scatter, use_container_width=True)

    # Extra info tonen
    st.write(f"Geselecteerde leeftijdsrange: {min_age} - {max_age}")
    st.write(f"Geselecteerde vlucht afstand: {min_dist} - {max_dist}")
    #-------------------Grafiek Lieke 2-----------------------
    #---------------------------------------------------------

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
    fig, ax = plt.subplots(figsize=(7,7), subplot_kw=dict(polar=True))

    # Kleur (consistent met dashboard)
    primary_color = "royalblue"

    # Lijn + vulling
    ax.plot(angles, scores, color=primary_color, linewidth=2)
    ax.fill(angles, scores, color=primary_color, alpha=0.25)

    # Stippen bij elke score
    ax.scatter(angles, scores, color=primary_color, s=40, zorder=5)

    # Waarden buiten de cirkel zetten (vast op rand + marge)
    r_outer = 5.2  # iets buiten maximale schaal
    for angle, score in zip(angles, scores):
        ax.text(angle, r_outer, f"{score:.1f}", 
                ha="center", va="center", fontsize=8, color="black")

    # Labels rond de cirkel verder naar buiten zetten
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(factors, fontsize=9)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("center")
    ax.tick_params(axis='x', pad=15)  # meer ruimte tussen labels en grafiek

    # Y-as schaal forceren: 0 in het midden, 5 aan de rand
    ax.set_ylim(0, 5)

    # Rasters en schaal aanpassen
    ax.set_rlabel_position(30)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=7, color="gray")
    ax.grid(color="lightgray", linestyle="--")

    # Titel
    plt.title("Gemiddelde scores per factor (Radar Chart)", size=12, pad=20)

    # Tonen in Streamlit
    st.pyplot(fig)




#-------------------page 3-----------------------------
#------------------------------------------------------
elif page == "Vliegtuig vs Trein":
    st.markdown(
        f"<h1 style='color:{primary_color}'>🚝 Klanttevredenheid Vliegtuig vs Trein</h1>",
        unsafe_allow_html=True)
    st.write("Hier is een vergelijking gemaakt tussen de klanttevredenheid van vliegtuigen (KLM) en treinen in Japan.")
    # Witregels
    st.write("")
    st.write("")
    # Titel
    st.title("Tevredenheid per categorie - Vliegtuig vs Trein")

    #-------------------Grafiek Koen vergelijking-------------
    #---------------------------------------------------------
    # Verwachte aspecten (labels)
    expected_aspects = [
        "Ease of Online booking", "Checkin service", "Online boarding",
        "Gate location", "On-board service", "Seat comfort",
        "Leg room service", "Cleanliness", "Food and drink",
        "Inflight service", "Inflight wifi service", "Inflight entertainment",
        "Baggage handling"
    ]


    def normalize(s: str) -> str:
        s = str(s).lower()
        return "".join(ch for ch in s if ch.isalnum())

    def get_common_aspects(df1: pd.DataFrame, df2: pd.DataFrame, expected_aspects):
        norm_to_col1 = {normalize(col): col for col in df1.columns if pd.notna(col)}
        norm_to_col2 = {normalize(col): col for col in df2.columns if pd.notna(col)}
        common = []
        for asp in expected_aspects:
            norm = normalize(asp)
            if norm in norm_to_col1 and norm in norm_to_col2:
                common.append((asp, norm_to_col1[norm], norm_to_col2[norm]))
        return common

    common_aspects = get_common_aspects(df, df_extra_aangepast, expected_aspects)

    if not common_aspects:
        st.warning("Geen gemeenschappelijke tevredenheidsaspecten gevonden.")
    else:
        labels = [asp for asp, _, _ in common_aspects]


        # Multiselect (standaard: alle aspecten)
        selected_labels = st.multiselect(
            "Kies de aspecten die je wilt vergelijken:",
            options=labels,
            default=labels
        )

        results = []
        for asp, col_air, col_train in common_aspects:
            if asp not in selected_labels:
                continue

            s_air = pd.to_numeric(df[col_air], errors="coerce") if col_air in df.columns else pd.Series(dtype="float64")
            s_train = pd.to_numeric(df_extra_aangepast[col_train], errors="coerce") if col_train in df_extra_aangepast.columns else pd.Series(dtype="float64")

            # Alleen meenemen als beide datasets numerieke waarden hebben
            if s_air.dropna().empty or s_train.dropna().empty:
                continue

            results.append({"Aspect": asp, "Dataset": "Vliegtuigen ✈️", "Score": round(float(s_air.mean()), 3)})
            results.append({"Aspect": asp, "Dataset": "Treinen 🚄", "Score": round(float(s_train.mean()), 3)})

        if not results:
            st.warning("Geen numerieke data gevonden voor de gemeenschappelijke aspecten.")
        else:
            results_df = pd.DataFrame(results)
            # Zorg dat Aspect in de gewenste volgorde blijft (alleen de geselecteerde labels)
            ordered_labels = [l for l in labels if l in selected_labels]
            results_df["Aspect"] = pd.Categorical(results_df["Aspect"], categories=ordered_labels, ordered=True)

            # Groeperende staafdiagram (side-by-side per aspect)
            chart = (
                alt.Chart(results_df)
                .mark_bar()
                .encode(
                    x=alt.X("Aspect:N", sort=ordered_labels, axis=alt.Axis(labelAngle=-45, labelFontSize=11)),
                    y=alt.Y("Score:Q", title="Gemiddelde score (0-5)"),
                    color=alt.Color("Dataset:N", legend=alt.Legend(title="Dataset")),
                    xOffset="Dataset:N",
                    tooltip=[alt.Tooltip("Aspect:N"), alt.Tooltip("Dataset:N"), alt.Tooltip("Score:Q")]
                )
                .properties(height=420)
            )

            st.altair_chart(chart, use_container_width=True)

#-------------------page 4-----------------------------
#-------------------------------------------------------
elif page == "Data Overzicht":
    st.markdown(f"<h1 style='color:{primary_color}'>✎ Data Overzicht</h1>", unsafe_allow_html=True)
    st.write("Op deze pagina zijn de gebruikte datasets te vinden. Onder ieder dataset staat de bijbehorende bron.")
    st.write("Hieronder is het  dataframe *airline_passenger_satisfaction.csv* te zien:")
    # Main dataframe laten zien
    st.dataframe(df)
    st.write("*Bron: Ahmad Bhat, M. (n.d.). Airline passenger satisfaction [Data set]. Kaggle.*")
    st.write("*https://www.kaggle.com/datasets/mysarahmadbhat/airline-passenger-satisfaction*")
    
    # Witregels
    st.write("")
    st.write("")
    st.write("")
    st.write("")

    st.write("Hieronder is het dataframe *Surveydata_test_(1).csv* te zien:")
    st.write("Wissel met het dropdown menu tussen het originele en het aangepaste dataset.")
    st.write("Zoals te zien is zijn de waardes omgezet naar een score tussen 0 en 5, waardoor er vergeleken kan worden met de scores van vliegtuigen.")
    st.write("Missende waardes zijn opgevuld met de mediaan van die kolom.")
    # Dropdown om te kiezen welk dataframe te tonen
    selected_df = st.selectbox(
        "Kies een dataset om te bekijken:",
        ["Origineel", "Aangepast"]
    )

    # Dataframe tonen afhankelijk van selectie
    if selected_df == "Origineel":
        st.dataframe(df_extra)
    else:
        st.dataframe(df_extra_aangepast)
    st.write("*Bron: Thejas2002. (n.d.). Shinkansen Travel Experience [Data set]. Kaggle.*")
    st.write("*https://www.kaggle.com/datasets/thejas2002/shinkansen-travel-experience*")


#-------------------page 5-----------------------------
#-------------------------------------------------------
elif page == "Werkwijze":
    st.markdown(f"<h1 style='color:{primary_color}'>✎ Werkwijze</h1>", unsafe_allow_html=True)
    st.write("Hier komt een beschrijving van hoe wij te werk zijn gegaan.")
