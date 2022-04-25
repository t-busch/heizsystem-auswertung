import streamlit as st
import pandas as pd
from io import BytesIO
from io import StringIO
import datetime
from dateutil import parser


st.set_page_config(
     page_title="WEM Auswertung",
     page_icon="🔥",
     layout="wide",
     initial_sidebar_state="expanded",
 )


TIME_PER_INTERVAL = 2/3*1/60 # kW in a 40s time interval to kWh 

def create_date_index(df):
    df.index = [parser.parse(f"{row.Date} {row.Time}") for _, row in df.iterrows()]
    return df

def file_to_df(uploaded_file, default_csv_name):
    bytes_data = uploaded_file.read()
    s=str(bytes_data,'utf-8')
    s = s.replace(",", ".")
    s = s.replace(";", ",")
    data = StringIO(s)
    df=pd.read_csv(data, error_bad_lines=False)

    # Save
    df.to_csv(default_csv_name)
    return df

def data_in_interval(df, start_date, end_date):
    df = df.loc[df.index>start_date, :]
    df = df.loc[df.index<=end_date, :]

    first_ts = max(min(df.index), start_date)
    last_ts = min(max(df.index), end_date)

    return df, first_ts, last_ts

def process_df(uploaded_file, start_date, end_date, default_csv_name=None):
    if uploaded_file is not None:
        df = file_to_df(uploaded_file, default_csv_name)
    else:
        df = pd.read_csv(default_csv_name, index_col=0)

    df.fillna(0, inplace=True)

    df = create_date_index(df)

    df, first_ts, last_ts = data_in_interval(df, start_date, end_date)
    return df, first_ts, last_ts

agg_type_dict = {"sum": "Summe", "av": "Mittelwert", "max": "Maximum", "min": "Minimum",}

def aggregate_data(df, col_name, unit="", aggr_type="sum", so=st):
    series_val = df.loc[:, col_name]
    aggr_val = float("NaN")
    if aggr_type == "sum":
        aggr_val = series_val.sum() * TIME_PER_INTERVAL
        aggr_val = aggr_val.round(1)
    so.metric(f"{agg_type_dict.get(aggr_type, '')} {col_name}", f"{aggr_val} {unit}")


current_year = datetime.datetime.now().year

uploaded_file=None


st.markdown("# Auswertung Heizsystem")

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
    df_bk,first_ts_bk, last_ts_bk = process_df(bk_file, start_date, end_date, default_csv_name="WTC_default.csv")
    df_wp, first_ts_wp, last_ts_wp = process_df(wp_file, start_date, end_date, default_csv_name="WWP_default.csv")
    

    cols = st.columns(2)

    cols[0].markdown("## Brennwertkessel")
    cols[1].markdown("## Wärmepumpe")
    print(df_wp.columns)

    # Auswertung BK
    col_index = 0
    cols[col_index].markdown(f"Erster gemessener Zeitschritt: {first_ts_bk}")
    cols[col_index].markdown(f"Letzter gemessener Zeitschritt: {last_ts_bk}")
    aggregate_data(df_bk, "Istleistung Aktuell[WE0]", unit="kWh", aggr_type="sum", so=cols[col_index])
    aggregate_data(df_bk, "Wärmeleistung VPT Aktuell[WE0]", unit="kWh", aggr_type="sum", so=cols[col_index])
    cols[col_index].write(df_bk)


    # Ausewrtung WP
    col_index=1
    cols[col_index].markdown(f"Erster gemessener Zeitschritt: {first_ts_wp}")
    cols[col_index].markdown(f"Letzter gemessener Zeitschritt: {last_ts_wp}")
    aggregate_data(df_wp, "Ist Leistung[Wärmeerzeuger ]", unit="kWh", aggr_type="sum", so=cols[col_index])
    aggregate_data(df_wp, "Leistungsabgabe[Wärmeerzeuger ]", unit="kWh", aggr_type="sum", so=cols[col_index])
    cols[col_index].write(df_wp)