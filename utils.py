import streamlit as st
import pandas as pd
from io import BytesIO
from io import StringIO
import plotly.graph_objects as go
import numpy as np

def temp_power(df):
    # df_res = pd.DataFrame(
    #     {
    #         "Außentemperatur": df.loc[:, "Außentemperatur"],
    #         "Wärmeleistung": df.loc[:, "Wärmeleistung"] * df.loc[:, "Timedelta"],
    #     }
    # )
    df_res = df.groupby(level=0, sort=True).sum()  # by="Außentemperatur" axis=0,
    return df_res