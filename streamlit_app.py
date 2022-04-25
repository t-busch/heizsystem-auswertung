import streamlit as st
import pandas as pd
from io import BytesIO
from io import StringIO
import datetime
from dateutil import parser
import plotly.graph_objects as go

st.set_page_config(
     page_title="WEM Auswertung",
     page_icon="🏠",
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
    so.metric(f"{agg_type_dict.get(aggr_type, '')}: {col_name}", f"{aggr_val} {unit}")


def actual_time_interval(first_ts, last_ts, so=st):
    so.info(f"Realer Betrachtungszeitraum:  \n {first_ts.strftime('%d.%m.%Y, %H:%M:%S')} bis {last_ts.strftime('%d.%m.%Y, %H:%M:%S')}")


current_year = datetime.datetime.now().year

uploaded_file=None


st.markdown("# Auswertung Heizsystem")

with st.sidebar:
    st.markdown("# Einstellungen")

    st.markdown("## WEM Daten-Upload")
    cols = st.columns(2)
    bk_file = cols[0].file_uploader("Brennwertkessel", type=["csv"], accept_multiple_files=False)
    wp_file = cols[1].file_uploader("Wärmepumpe", type=["csv"], accept_multiple_files=False)

    st.markdown("## Betrachtungszeitraum")
    cols = st.columns(2)
    start_date = cols[0].date_input("von", value=datetime.date(current_year-1, 8, 1))
    start_date = datetime.datetime.fromordinal(start_date.toordinal())
    end_date = cols[1].date_input("bis", value=datetime.date(current_year, 7, 31))
    end_date = datetime.datetime.fromordinal(end_date.toordinal())

    start_analysis = st.button("Auswertung starten")


if start_analysis:
    df_bk,first_ts_bk, last_ts_bk = process_df(bk_file, start_date, end_date, default_csv_name="WTC_default.csv")
    df_wp, first_ts_wp, last_ts_wp = process_df(wp_file, start_date, end_date, default_csv_name="WWP_default.csv")
    df_wp.loc[:, "Leistungsabgabe[Wärmeerzeuger ]"] = df_wp.loc[:, "Leistungsabgabe[Wärmeerzeuger ]"]/1000 # W in kW

    cols = st.columns(2)

    cols[0].markdown("## Brennwertkessel 🔥")
    cols[1].markdown("## Wärmepumpe 🔌")

    # Auswertung BK
    col_index = 0
    actual_time_interval(first_ts_bk, last_ts_bk, so=cols[col_index])
    # aggregate_data(df_bk, "Istleistung Aktuell[WE0]", unit="kWh", aggr_type="sum", so=cols[col_index])
    aggregate_data(df_bk, "Wärmeleistung VPT Aktuell[WE0]", unit="kWh", aggr_type="sum", so=cols[col_index])

    # Ausewrtung WP
    col_index=1
    actual_time_interval(first_ts_wp, last_ts_wp, so=cols[col_index])
    # aggregate_data(df_wp, "Ist Leistung[Wärmeerzeuger ]", unit="kWh", aggr_type="sum", so=cols[col_index])
    aggregate_data(df_wp, "Leistungsabgabe[Wärmeerzeuger ]", unit="kWh", aggr_type="sum", so=cols[col_index])


    fig = go.Figure()
    xvals = df_bk.index

    col_name = "Istleistung Aktuell[WE0]"
    # fig.add_trace(
    #     go.Scatter(
    #         x=xvals,
    #         y=df_bk.loc[:, col_name],
    #         name="BK_"+col_name,
    #         line=dict(
    #             #color=FZJcolor.get("black"), 
    #             width=2,),
    #         fillcolor="rgba(0, 0, 0, 0)",
    #     )
    # )

    col_name = "Wärmeleistung VPT Aktuell[WE0]"
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_bk.loc[:, col_name],
            name="BK_"+col_name,
            line=dict(
                #color=FZJcolor.get("black"), 
                width=2,),
            fillcolor="rgba(0, 0, 0, 0)",
        )
    )

    xvals = df_wp.index
    # col_name = "Ist Leistung[Wärmeerzeuger ]"
    # fig.add_trace(
    #     go.Scatter(
    #         x=xvals,
    #         y=df_wp.loc[:, col_name],
    #         name="WP_"+col_name,
    #         line=dict(
    #             #color=FZJcolor.get("black"), 
    #             width=2,),
    #         fillcolor="rgba(0, 0, 0, 0)",
    #     )
    # )

    col_name = "Leistungsabgabe[Wärmeerzeuger ]"
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_wp.loc[:, col_name],
            name="WP_"+col_name,
            line=dict(
                #color=FZJcolor.get("black"), 
                width=2,),
            fillcolor="rgba(0, 0, 0, 0)",
            # visible='legendonly',
        )
    )

    fig.update_layout(
        title=f"Wärmebereitstellung",
        yaxis_title="Leistung [kW]",
        # yaxis_range=[0, 1200],
        # xaxis_range=[start_date, end_date],
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Rohdaten")
    cols = st.columns(2)
    cols[0].write(df_bk)
    cols[1].write(df_wp)