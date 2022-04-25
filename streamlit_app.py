import streamlit as st
import pandas as pd
from io import BytesIO
from io import StringIO
import datetime
from dateutil import parser

st.markdown("# Auswertung Heizsystem")

TIME_PER_INTERVAL = 2/3*1/60 # kW in a 40s time interval to kWh 


uploaded_file=None

with st.sidebar:
    st.markdown("# Einstellungen")
    uploaded_file = st.file_uploader("Datei hochladen", type=["csv"], accept_multiple_files=False)

    start_analysis = st.button("Auswertung starten")

if start_analysis:
    print(type(uploaded_file))
    bytes_data = uploaded_file.read()
    s=str(bytes_data,'utf-8')
    s = s.replace(",", ".")
    s = s.replace(";", ",")
    data = StringIO(s)
    df=pd.read_csv(data, error_bad_lines=False)
    print(type(bytes_data))
    df.to_csv("test.csv")

df= pd.read_csv("test.csv", index_col=0)

df.index = [parser.parse(f"{row.Date} {row.Time}") for _, row in df.iterrows()]

# Istleistung Aktuell[WE0]
total_energy = df.loc[:, "Istleistung Aktuell[WE0]"].sum() * TIME_PER_INTERVAL
total_energy = total_energy.round(1)
st.metric("Summe Istleistung Aktuell[WE0]", f"{total_energy} kWh")

total_energy1 = df.loc[:, "Wärmeleistung VPT Aktuell[WE0]"].sum() * TIME_PER_INTERVAL
total_energy1 = total_energy1.round(1)
st.metric("Summe Wärmeleistung VPT Aktuell[WE0]", f"{total_energy1} kWh")


st.write(df)

