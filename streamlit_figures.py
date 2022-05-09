import streamlit as st
import pandas as pd
from io import BytesIO
from io import StringIO
import plotly.graph_objects as go
import numpy as np
import utils as ut

def power_line(df_bk, df_wp, so=st):
    fig = go.Figure()
    col_name = "Wärmeleistung"

    xvals = df_bk.index
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_bk.loc[:, col_name],
            name="BK_" + col_name,
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
            name="WP_" + col_name,
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

    so.plotly_chart(fig, use_container_width=True)


def power_area(df_bk, df_wp, so=st):
    fig = go.Figure()
    col_name = "Wärmeleistung"

    xvals = df_bk.index
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_bk.loc[:, col_name],
            name="BK_" + col_name,
            stackgroup="one",
            mode="none",
        )
    )

    xvals = df_wp.index
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_wp.loc[:, col_name],
            name="WP_" + col_name,
            stackgroup="one",
            mode="none",
        )
    )

    fig.update_layout(
        title=f"Wärmeleistung (gesamt)",
        yaxis_title="Wärmeleistung [kW]",
        yaxis_range=[0, 20],
        # xaxis_range=[start_date, end_date],
    )

    so.plotly_chart(fig, use_container_width=True)


def rel_power_line(df_bk, df_wp, so=st):
    fig = go.Figure()
    col_name = "Leistungsfaktor"

    xvals = df_bk.index
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_bk.loc[:, col_name],
            name="BK_" + col_name,
            line=dict(
                # color=FZJcolor.get("black"),
                width=2,
            ),
            fillcolor="rgba(0, 0, 0, 0)",
        )
    )

    xvals = df_wp.index
    fig.add_trace(
        go.Scatter(
            x=xvals,
            y=df_wp.loc[:, col_name],
            name="WP_" + col_name,
            line=dict(
                # color=FZJcolor.get("black"),
                width=2,
            ),
            fillcolor="rgba(0, 0, 0, 0)",
        )
    )

    fig.update_layout(
        title=f"Leistungsfaktor",
        yaxis_title="Leistungsfaktor [%]",
        yaxis_range=[0, 100],
        # xaxis_range=[start_date, end_date],
    )
    so.plotly_chart(fig, use_container_width=True)


def temp_area(df_temp_bk, df_temp_wp, so=st):

    fig = go.Figure()

    temp_power_bk = ut.temp_power(df_temp_bk)
    fig.add_trace(
        go.Scatter(
            x=temp_power_bk.index,
            y=temp_power_bk.loc[:, "Wärmemenge"],
            name=f"BK_Wärmemenge",
            # line=dict(
            #     #color=FZJcolor.get("black"),
            #     width=2,),
            stackgroup="one",
            mode="none",
        )
    )

    temp_power_wp = ut.temp_power(df_temp_wp)
    print(temp_power_wp.head())
    fig.add_trace(
        go.Scatter(
            x=temp_power_wp.index,
            y=temp_power_wp.loc[:, "Wärmemenge"],
            name=f"WP_Wärmemenge",
            # line=dict(
            #     #color=FZJcolor.get("black"),
            #     width=2,),
            stackgroup="one",
            mode="none",
        )
    )

    fig.update_layout(
        title=f"Wärmemenge vs. Außentemperatur",
        yaxis_title="Wärmemenge [kWh]",
        xaxis_title="Außentemperatur [°C]",
        # yaxis_range=[0, 100],
        # xaxis_range=[start_date, end_date],
    )
    so.plotly_chart(fig, use_container_width=True)