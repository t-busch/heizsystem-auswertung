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
    # TODO not recognizing date correctly, manuelle funktion
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
    df.sort_index(axis=0, inplace=True)
    df = df.loc[df.index>start_date, :]
    df = df.loc[df.index<=end_date, :]

    print(min(df.index))
    print(min(df.index) in df.index)
    print(max(df.index))
    print(max(df.index) in df.index)
    print(df.index)

    first_ts = max(min(df.index), start_date)
    last_ts = min(max(df.index), end_date)
    

    return df, first_ts, last_ts

def proprocess_df(uploaded_file, start_date, end_date, default_csv_name=None):
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
    elif aggr_type == "av":
        aggr_val = series_val.mean()

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
    start_date = cols[0].date_input("von", value=datetime.date(current_year-1, 9, 1))
    start_date = datetime.datetime.fromordinal(start_date.toordinal())+datetime.timedelta(hours=0, minutes=0, seconds=0)
    end_date = cols[1].date_input("bis", value=datetime.date(current_year, 8, 31))
    end_date = datetime.datetime.fromordinal(end_date.toordinal())+datetime.timedelta(hours=23, minutes=59, seconds=59)

    start_analysis = st.button("Auswertung starten")


def process_bk(df_raw):
    df = pd.DataFrame(index=df_raw.index)
    df.loc[:, "Wärmeleistung"] = df_raw.loc[:, "Wärmeleistung VPT Aktuell[WE0]"] # kW
    df.loc[:, "Leistungsfaktor"] = df_raw.loc[:, "Istleistung Aktuell[WE0]"] # %
    df.loc[:, "Außentemperatur"] = df_raw.loc[:, "Außentemperatur Aktuell[SYSTEM0]"] # °C
    return df

def process_wp(df_raw):
    df = pd.DataFrame(index=df_raw.index)
    df.loc[:, "Wärmeleistung"] = df_raw.loc[:, "Leistungsabgabe[Wärmeerzeuger ]"]/1000 # kW
    df.loc[:, "Leistungsfaktor"] = df_raw.loc[:, "Ist Leistung[Wärmeerzeuger ]"] # %
    df.loc[:, "Außentemperatur"] = df_raw.loc[:, "Außentemperatur[Wärmeerzeuger ]"] # %
    return df


def temp_power(df):
    df_res = pd.DataFrame({"Außentemperatur": df.loc[:, "Außentemperatur"], "Wärmeleistung": df.loc[:, "Wärmeleistung"]})
    df_res = df_res.groupby(by="Außentemperatur", axis=0, sort=True).sum()
    return df_res

if True: #start_analysis:
    df_bk_raw, first_ts_bk, last_ts_bk = proprocess_df(bk_file, start_date, end_date, default_csv_name="WTC_default.csv")
    # st.write(df_bk_raw.columns)
    df_bk = process_bk(df_bk_raw)

    df_wp_raw, first_ts_wp, last_ts_wp = proprocess_df(wp_file, start_date, end_date, default_csv_name="WWP_default.csv")
    # st.write(df_wp_raw.columns)
    df_wp = process_wp(df_wp_raw)


    cols = st.columns(2)
    cols[0].markdown("## Brennwertkessel 🔥")
    cols[1].markdown("## Wärmepumpe 🔌")

    # Auswertung BK
    col_index = 0
    actual_time_interval(first_ts_bk, last_ts_bk, so=cols[col_index])
    aggregate_data(df_bk, "Wärmeleistung", unit="kWh", aggr_type="sum", so=cols[col_index])
    aggregate_data(df_bk, "Leistungsfaktor", unit="%", aggr_type="av", so=cols[col_index])

    # Ausewrtung WP
    col_index=1
    actual_time_interval(first_ts_wp, last_ts_wp, so=cols[col_index])
    aggregate_data(df_wp, "Wärmeleistung", unit="kWh", aggr_type="sum", so=cols[col_index])
    aggregate_data(df_wp, "Leistungsfaktor", unit="%", aggr_type="av", so=cols[col_index])


    # Absolute Leistung
    fig = go.Figure()
    col_name = "Wärmeleistung"
    
    xvals = df_bk.index
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_bk.loc[:, col_name],
            name="BK_"+col_name,
            # line=dict(
            #     #color=FZJcolor.get("black"), 
            #     width=2,),
            # fillcolor="rgba(0, 0, 0, 0)",
        )
    )

    xvals = df_wp.index
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_wp.loc[:, col_name],
            name="WP_"+col_name,
            # line=dict(
            #     #color=FZJcolor.get("black"), 
            #     width=2,),
            # fillcolor="rgba(0, 0, 0, 0)",
            # visible='legendonly',
        )
    )

    fig.update_layout(
        title=f"Wärmeleistung",
        yaxis_title="Wärmeleistung [kW]",
        # yaxis_range=[0, 1200],
        # xaxis_range=[start_date, end_date],
    )

    st.plotly_chart(fig, use_container_width=True)


    # Wärmeleistung ges
    fig = go.Figure()
    col_name = "Wärmeleistung"
    
    xvals = df_bk.index
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_bk.loc[:, col_name],
            name="BK_"+col_name,
            stackgroup="one",
            mode="none",
        )
    )

    xvals = df_wp.index
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_wp.loc[:, col_name],
            name="WP_"+col_name,
            stackgroup="one",
            mode="none",
        )
    )

    fig.update_layout(
        title=f"Wärmeleistung (gesamt)",
        yaxis_title="Wärmeleistung [kW]",
        # yaxis_range=[0, 1200],
        # xaxis_range=[start_date, end_date],
    )

    st.plotly_chart(fig, use_container_width=True)

    # Relative Leistung
    fig = go.Figure()
    col_name = "Leistungsfaktor"
    
    xvals = df_bk.index
    print(xvals)
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
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_wp.loc[:, col_name],
            name="WP_"+col_name,
            line=dict(
                #color=FZJcolor.get("black"), 
                width=2,),
            fillcolor="rgba(0, 0, 0, 0)",
        )
    )

    fig.update_layout(
        title=f"Leistungsfaktor",
        yaxis_title="Leistungsfaktor [%]",
        yaxis_range=[0, 100],
        # xaxis_range=[start_date, end_date],
    )
    st.plotly_chart(fig, use_container_width=True)



    # Temperatur-Leistung

    # TODO Group by temperature and apply sum()
    fig = go.Figure()

    temp_power_bk = temp_power(df_bk)
    fig.add_trace(
        go.Scatter(
            x=temp_power_bk.index,
            y=temp_power_bk.loc[:, "Wärmeleistung"],
            name=f"BK_Wärmeleistung",
            # line=dict(
            #     #color=FZJcolor.get("black"), 
            #     width=2,),
            stackgroup="one",
            mode="none",
        )
    )

    temp_power_wp = temp_power(df_wp)
    fig.add_trace(
        go.Scatter(
            x=temp_power_wp.index,
            y=temp_power_wp.loc[:, "Wärmeleistung"],
            name=f"WP_Wärmeleistung",
            # line=dict(
            #     #color=FZJcolor.get("black"), 
            #     width=2,),
            stackgroup="one",
            mode="none",
        )
    )

    fig.update_layout(
        title=f"Wärmeleistung vs. Außentemperatur",
        yaxis_title="Wärmeleistung [kW]",
        xaxis_title="Außentemperatur [°C]",
        # yaxis_range=[0, 100],
        # xaxis_range=[start_date, end_date],
    )
    st.plotly_chart(fig, use_container_width=True)


    st.markdown("### Rohdaten")
    cols = st.columns(2)
    cols[0].write(df_bk_raw)
    cols[0].write(df_bk)
    cols[1].write(df_wp_raw)
    cols[1].write(df_wp)