#-------------------imports-----------------------------
#-------------------------------------------------------
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
    df_extra = pd.read_csv("airlines_flights_data.csv")
    return df_extra

df_extra = load_extra_data()

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
    page = st.selectbox("Selecteer een pagina", ["Snel Overzicht", "Dashboard", "Data Overzicht", "Werkwijze"])

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
    st.write("*23:39 - 23 sep 2025*")

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
    st.write("Filter hier op vertraagde vluchten.")
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
        title="Satisfaction per Customer Type en Type of Travel",
        color_discrete_sequence=[primary_color, "lightcoral"]
    )
    fig.update_layout(xaxis_title="Customer Type & Type of Travel", yaxis_title="Aantal passagiers", legend_title="Satisfaction")
    st.plotly_chart(fig, use_container_width=True)
    #-------------------Grafiek Koen---------------------------
    #---------------------------------------------------------
    # Titel
    st.title("Airline Satisfaction Dashboard")

    # Dropdown voor Class-selectie
    class_options = df["Class"].dropna().unique()
    selected_class = st.selectbox("Kies een Class:", sorted(class_options))

    # Filter voor vertraagde vluchten
    delay_filter = st.checkbox("Toon alleen vertraagde vluchten ✈️", value=False)

    # Kolommen die we willen analyseren
    aspects = [
       "Ease of Online booking", "Checkin service", "Online boarding",
        "Gate location", "On-board service", "Seat comfort",
        "Leg room service", "Cleanliness", "Food and drink",
        "Inflight service", "Inflight wifi service", "Inflight entertainment",
        "Baggage handling"
    ]

    st.write("Kies de aspecten die je wilt zien:")
    selected_aspects = []
    for aspect in aspects:
        if st.checkbox(aspect, value=True):  # standaard allemaal aangevinkt
            selected_aspects.append(aspect)

    # Data filteren op gekozen class
    filtered_df = df[df["Class"] == selected_class]

    # Extra filter op vertraagde vluchten
    if delay_filter and "Flight Status" in df.columns:
        filtered_df = filtered_df[filtered_df["Flight Status"] == "Delayed"]

    # Alleen bestaande kolommen gebruiken
    valid_aspects = [col for col in selected_aspects if col in filtered_df.columns]

    if valid_aspects:
       mean_values = filtered_df[valid_aspects].mean()
       st.bar_chart(mean_values)
    else:
        st.warning("Geen geldige aspecten geselecteerd of kolommen ontbreken in de dataset.")


#-------------------page 3-----------------------------
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

    st.write("Hieronder is het dataframe *airlines_flights_data.csv* te zien:")
    # Extra dataframe laten zien
    st.dataframe(df_extra)
    st.write("*Bron: Grewal, R. (n.d.). Airlines flights data [Data set]. Kaggle.*")
    st.write("*https://www.kaggle.com/datasets/rohitgrewal/airlines-flights-data*")

#-------------------page 4-----------------------------
#-------------------------------------------------------
elif page == "Werkwijze":
    st.markdown(f"<h1 style='color:{primary_color}'>✎ Werkwijze</h1>", unsafe_allow_html=True)
    st.write("Hier komt een beschrijving van hoe wij te werk zijn gegaan.")
