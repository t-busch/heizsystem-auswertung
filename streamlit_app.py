import streamlit as st
import pandas as pd
from io import BytesIO
from io import StringIO
import datetime
from dateutil import parser
import plotly.graph_objects as go
import numpy as np
import streamlit_figures as stfig
import utils as ut


st.set_page_config(
    page_title="WEM Auswertung",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)


TIME_PER_INTERVAL = 2 / 3 * 1 / 60  # kW in a 40s time interval to kWh


def create_date(date, time):
    date = str(date)
    time = str(time)
    day = int(date.split(".")[0])
    month = int(date.split(".")[1])
    year = int(date.split(".")[2])
    hour = int(time.split(":")[0])
    minute = int(time.split(":")[1])
    second = int(time.split(":")[2])
    datetime_val = datetime.datetime(year, month, day, hour, minute, second)
    return datetime_val


def create_date_index(df):
    df.index = [create_date(row.Date, row.Time) for _, row in df.iterrows()]
    return df


def file_to_df(uploaded_file, default_csv_name):
    bytes_data = uploaded_file.read()
    s = str(bytes_data, "utf-8")
    s = s.replace(",", ".")
    s = s.replace(";", ",")
    data = StringIO(s)
    df = pd.read_csv(data, error_bad_lines=False)

    # Save
    df.to_csv(default_csv_name)
    return df


def data_in_interval(df, start_date, end_date):
    df.sort_index(axis=0, inplace=True)
    df = df.loc[df.index > start_date, :]
    df = df.loc[df.index <= end_date, :]

    first_ts = max(min(df.index), start_date)
    last_ts = min(max(df.index), end_date)

    return df, first_ts, last_ts


def preprocess_df(uploaded_file, start_date, end_date, default_csv_name=None):
    if uploaded_file is not None:
        df = file_to_df(uploaded_file, default_csv_name)
    else:
        df = pd.read_csv(default_csv_name, index_col=0)

    df.fillna(0, inplace=True)

    df = create_date_index(df)

    df, first_ts, last_ts = data_in_interval(df, start_date, end_date)
    return df, first_ts, last_ts


def interpolate_timesteps(df_base, df_interpol):
    df_base.loc[:, "Timestamp"] = df_base.index
    df_base = df_base.append(
        pd.DataFrame({"Timestamp": list(df_interpol.index)}), ignore_index=True
    )
    df_base.index = df_base.loc[:, "Timestamp"]
    df_base.sort_index(inplace=True)
    del df_base["Timestamp"]
    for col in df_base.columns:
        df_base.loc[:, col] = df_base.loc[:, col].interpolate()
    df_base.fillna(0, inplace=True)
    return df_base


def harmonize_timesteps(df_bk, df_wp):
    # all_timesteps = list(df_wp.index) + list(df_bk.index)
    df_bk = interpolate_timesteps(df_bk, df_wp)
    df_wp = interpolate_timesteps(df_wp, df_bk)
    return df_bk, df_wp


def aggregate_data(df, col_name, unit="", aggr_type="sum", so=st):
    agg_type_dict = {
        "sum": "Summe",
        "av": "Mittelwert",
        "max": "Maximum",
        "min": "Minimum",
    }
    series_val = df.loc[:, col_name]
    timedelta = df.loc[:, "Timedelta"]
    aggr_val = float("NaN")
    if aggr_type == "sum":
        aggr_val = sum(series_val * timedelta)
    elif aggr_type == "av":
        aggr_val = sum(series_val * timedelta) / timedelta.sum()

    aggr_val = round(aggr_val, 1)
    so.metric(f"{agg_type_dict.get(aggr_type, '')}: {col_name}", f"{aggr_val} {unit}")


def actual_time_interval(first_ts, last_ts, so=st):
    so.info(
        f"Realer Betrachtungszeitraum:  \n {first_ts.strftime('%d.%m.%Y, %H:%M:%S')} bis {last_ts.strftime('%d.%m.%Y, %H:%M:%S')}"
    )


current_year = datetime.datetime.now().year

uploaded_file = None


st.markdown("# Auswertung Heizsystem")

with st.sidebar:
    st.markdown("# Einstellungen")

    st.markdown("## WEM Daten-Upload")
    cols = st.columns(2)
    bk_file = cols[0].file_uploader(
        "Brennwertkessel", type=["csv"], accept_multiple_files=False
    )
    wp_file = cols[1].file_uploader(
        "Wärmepumpe", type=["csv"], accept_multiple_files=False
    )

    st.markdown("## Betrachtungszeitraum")
    cols = st.columns(2)

    # Start at the beginning of the day (00:00:00)
    start_date = cols[0].date_input("von", value=datetime.date(current_year - 1, 9, 1))
    start_date = datetime.datetime.fromordinal(
        start_date.toordinal()
    ) + datetime.timedelta(hours=0, minutes=0, seconds=0)

    # Stop at the end of the day (23:59:59)
    end_date = cols[1].date_input("bis", value=datetime.date(current_year, 8, 31))
    end_date = datetime.datetime.fromordinal(end_date.toordinal()) + datetime.timedelta(
        hours=23, minutes=59, seconds=59
    )

    start_analysis = st.button("Auswertung starten")


def process_bk(df_raw):
    df = pd.DataFrame(index=df_raw.index)
    df.loc[:, "Wärmeleistung"] = df_raw.loc[:, "Wärmeleistung VPT Aktuell[WE0]"]  # kW
    df.loc[:, "Leistungsfaktor"] = df_raw.loc[:, "Istleistung Aktuell[WE0]"]  # %
    df.loc[:, "Außentemperatur"] = df_raw.loc[
        :, "Außentemperatur Aktuell[SYSTEM0]"
    ]  # °C
    return df


def process_wp(df_raw):
    df = pd.DataFrame(index=df_raw.index)
    df.loc[:, "Wärmeleistung"] = (
        df_raw.loc[:, "Leistungsabgabe[Wärmeerzeuger ]"] / 1000
    )  # kW
    df.loc[:, "Leistungsfaktor"] = df_raw.loc[:, "Ist Leistung[Wärmeerzeuger ]"]  # %
    df.loc[:, "Außentemperatur"] = df_raw.loc[:, "Außentemperatur[Wärmeerzeuger ]"]  # %
    return df


def add_timedelta(df):
    timestep = list(df.index)
    timedelta = [timestep[n + 1] - timestep[n] for n in range(len(timestep) - 1)]
    timedelta = [x.seconds / 3600 for x in timedelta] + [TIME_PER_INTERVAL]
    df.loc[:, "Timedelta"] = timedelta
    return df


def interpolate_temp(df, step):
    col_interpol = "Außentemperatur"
    df.loc[:, "Wärmemenge"] = df.loc[:, "Wärmeleistung"] * TIME_PER_INTERVAL
    if step:
        temps = df.loc[:, col_interpol]
        temps_interpol = np.arange(min(temps), max(temps), step)

        # exclude duplicates
        temps_interpol = [temp for temp in temps_interpol if temp not in temps]

        # add interpolated timesteps
        df_interpol = df.append(
            pd.DataFrame({col_interpol: list(temps_interpol)}), ignore_index=True
        )
    else:
        df_interpol = df.copy()

    # set temps as index
    df_interpol.index = df_interpol.loc[:, col_interpol]
    df_interpol.sort_index(inplace=True)
    del df_interpol[col_interpol]

    # apply interpolation
    for col in df_interpol.columns:
        scalefac = sum(df.loc[:, col]) / sum(df_interpol.loc[:, col])
        df_interpol.loc[:, col] = df_interpol.loc[:, col].interpolate() * scalefac
    df_interpol.fillna(0, inplace=True)
    return df_interpol


if True:  # start_analysis:
    # Data preprocessing
    df_bk_raw, first_ts_bk, last_ts_bk = preprocess_df(
        bk_file, start_date, end_date, default_csv_name="WTC_default.csv"
    )

    df_wp_raw, first_ts_wp, last_ts_wp = preprocess_df(
        wp_file, start_date, end_date, default_csv_name="WWP_default.csv"
    )

    # Data processing
    df_bk = process_bk(df_bk_raw)
    df_wp = process_wp(df_wp_raw)

    # Temp Power Data
    df_temp_bk = interpolate_temp(df_bk, 0.1)
    df_temp_wp = interpolate_temp(df_wp, 0.1)

    # Interpolate Timesteps
    df_bk, df_wp = harmonize_timesteps(df_bk, df_wp)

    # Add Timedelta
    df_bk = add_timedelta(df_bk)
    df_wp = add_timedelta(df_wp)

    cols = st.columns(2)
    cols[0].markdown("## Brennwertkessel 🔥")
    cols[1].markdown("## Wärmepumpe 🔌")

    # Auswertung BK
    col_index = 0
    actual_time_interval(first_ts_bk, last_ts_bk, so=cols[col_index])
    aggregate_data(
        df_bk, "Wärmeleistung", unit="kWh", aggr_type="sum", so=cols[col_index]
    )
    aggregate_data(
        df_bk, "Leistungsfaktor", unit="%", aggr_type="av", so=cols[col_index]
    )

    # Ausewrtung WP
    col_index = 1
    actual_time_interval(first_ts_wp, last_ts_wp, so=cols[col_index])
    aggregate_data(
        df_wp, "Wärmeleistung", unit="kWh", aggr_type="sum", so=cols[col_index]
    )
    aggregate_data(
        df_wp, "Leistungsfaktor", unit="%", aggr_type="av", so=cols[col_index]
    )

    # Absolute Leistung
    stfig.power_line(df_bk, df_wp)

    # Wärmeleistung ges
    stfig.power_area(df_bk, df_wp)

    # Relative Leistung
    stfig.rel_power_line(df_bk, df_wp)

    # Temperatur-Leistung
    # TODO Besser als scatter plot
    stfig.temp(df_bk, df_wp)

    st.markdown("### Rohdaten")
    cols = st.columns(2)
    cols[0].write(df_bk_raw)
    cols[0].write(df_bk)
    cols[1].write(df_wp_raw)
    cols[1].write(df_wp)
