# %%
import pandas as pd
import numpy as np 
import matplotlib. pyplot as plt 
import plotly.express as px
import streamlit as st
import seaborn as sns
import matplotlib.cm as cm



# %%
df1 = pd.read_csv("airline_passenger_satisfaction.csv", header=0, sep="," )
print(df1.to_string())



# %%
df2 = pd.read_csv("data_dictionary.csv", header=0, sep=",")
print(df2.to_string())


# %%
df3 = pd.read_csv("airlines_flights_data.csv", header=0, sep=",")
print(df3.to_string())

# %%
print(df1.isnull().sum())


# %%
print(df2.isnull().sum())

# %%
print(df3.isnull().sum())

# %%
print(df1[['Gender','Class','Satisfaction']])


# %%
df1['Gender_Class'] = df1['Gender'] + ' | ' + df1['Class']
unique_combos = df1['Gender_Class'].unique()
n = len(unique_combos)
jet_colors = cm.jet(np.linspace(0, 1, n))
palette = dict(zip(unique_combos, jet_colors))

sns.boxplot(x="Gender_Class", y="Satisfaction", data=df1, palette=palette)
plt.title("Satisfaction by Gender and Class")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()




# %%
plt.figure(figsize=(12,6))
sns.countplot(x='Gender_Class', hue='Satisfaction', data=df1)
plt.title("Aantal per Gender-Class en Satisfaction")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# %%
# Mapping met 2 scores
score_map = {
    'Dissatisfied': 1,
    'Neutral': 1,
    'Satisfied': 2
}

# Nieuwe kolom met numerieke scores maken
df1['Satisfaction_score'] = df1['Satisfaction'].map(score_map)

# Check of alles goed is
print(df1[['Satisfaction', 'Satisfaction_score']].head())

# Boxplot tekenen
plt.figure(figsize=(12,6))
sns.boxplot(x='Gender_Class', y='Satisfaction_score', data=df1, palette=palette)
plt.title("Satisfaction by Gender and Class (2 Scores)")
plt.xticks(rotation=45)

# Y-as labels aanpassen
plt.yticks([1, 2], ['Dissatisfied or Neutral', 'Satisfied'])

plt.tight_layout()
plt.show()




