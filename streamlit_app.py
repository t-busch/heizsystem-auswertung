import streamlit as st
import pandas as pd
from io import BytesIO
from io import StringIO
import datetime
from dateutil import parser

st.markdown("# Auswertung Heizsystem")

TIME_PER_INTERVAL = 2/3*1/60 # kW in a 40s time interval to kWh 

def create_date_index(df):
    df.index = [parser.parse(f"{row.Date} {row.Time}") for _, row in df.iterrows()]
    return df

def file_to_df(uploaded_file):
    bytes_data = uploaded_file.read()
    s=str(bytes_data,'utf-8')
    s = s.replace(",", ".")
    s = s.replace(";", ",")
    data = StringIO(s)
    df=pd.read_csv(data, error_bad_lines=False)
    return df

def data_in_interval(df, start_date, end_date):
    df = df.loc[df.index>start_date, :]
    df = df.loc[df.index<=end_date, :]
    return df

def process_df(uploaded_file, start_date, end_date):
    df = file_to_df(uploaded_file)

    df.fillna(0, inplace=True)

    df = create_date_index(df)

    df = data_in_interval(df, start_date, end_date)
    return df


current_year = datetime.datetime.now().year

uploaded_file=None

with st.sidebar:
    st.markdown("# Einstellungen")

    st.markdown("## Datei-Upload")
    cols = st.columns(2)
    bk_file = cols[0].file_uploader("Brennwertkessel", type=["csv"], accept_multiple_files=False)
    wp_file = cols[1].file_uploader("Wärmepumpe", type=["csv"], accept_multiple_files=False)

    st.markdown("## Betrachtungszeitraum")
    cols = st.columns(2)
    start_date = cols[0].date_input("Start", value=datetime.date(current_year-1, 8, 1))
    start_date = datetime.datetime.fromordinal(start_date.toordinal())
    end_date = cols[1].date_input("Ende", value=datetime.date(current_year, 7, 31))
    end_date = datetime.datetime.fromordinal(end_date.toordinal())

    start_analysis = st.button("Auswertung starten")


if start_analysis:
    df_bk = process_df(bk_file, start_date, end_date)
    df_wp = process_df(wp_file, start_date, end_date)

    cols = st.columns(2)

    cols[0].markdown("## Brennwertkessel")
    cols[1].markdown("## Wärmepumpe")
    print(df_wp.columns)

    # Istleistung Aktuell[WE0]
    total_energy = df_bk.loc[:, "Istleistung Aktuell[WE0]"].sum() * TIME_PER_INTERVAL
    total_energy = total_energy.round(1)
    cols[0].metric("Summe Istleistung Aktuell[WE0]", f"{total_energy} kWh")

    total_energy1 = df_bk.loc[:, "Wärmeleistung VPT Aktuell[WE0]"].sum() * TIME_PER_INTERVAL
    total_energy1 = total_energy1.round(1)
    cols[0].metric("Summe Wärmeleistung VPT Aktuell[WE0]", f"{total_energy1} kWh")

    cols[0].write(df_bk)

