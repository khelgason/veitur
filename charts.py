import plotly.graph_objects as go
import streamlit as st
import numpy as np
import pandas as pd
from utils import COLORS, get_icelandic_month

def add_cost_bars(fig, df, prefix):
    """
    Add stacked cost bars to a Plotly figure.
    Used by both electricity and hot water charts.
    """
    # Create a custom hover template that shows the total cost with Icelandic date format
    hovertemplate = 'Dagsetning: %{customdata[1]}<br>Heildarkostnaður: %{customdata[0]:,.0f} kr.<extra></extra>'
    
    # Create formatted Icelandic dates for hover
    icelandic_dates = []
    for d in df["date"]:
        day = d.day
        month = get_icelandic_month(d.month)
        icelandic_dates.append(f"{day}. {month} {d.year}")
    
    # Create array of [total_cost, icelandic_date] for each point
    hover_data = list(zip(df[f"{prefix}_total"], icelandic_dates))
    
    # Add the cost components as stacked bars
    fig.add_trace(go.Bar(
        x=df["date"], 
        y=df["cost_fixed"], 
        name="Fastur kostnaður", 
        marker_color=COLORS["mid_gray"],
        customdata=hover_data,  # Pass total cost and formatted date for hover
        hovertemplate=hovertemplate
    ))
    
    fig.add_trace(go.Bar(
        x=df["date"], 
        y=df["cost_equalization"], 
        name="Jöfnunargjald", 
        marker_color=COLORS["mid_light_gray"],
        customdata=hover_data,  # Pass total cost and formatted date for hover
        hovertemplate=hovertemplate
    ))
    
    fig.add_trace(go.Bar(
        x=df["date"], 
        y=df[f"{prefix}_tax"], 
        name="Skattar", 
        marker_color=COLORS["dark_gray"],
        customdata=hover_data,  # Pass total cost and formatted date for hover
        hovertemplate=hovertemplate
    ))
    
    # Use different colors for electricity vs water usage
    color = COLORS["red"] if prefix == "elec" else COLORS["dark_blue"]
    
    fig.add_trace(go.Bar(
        x=df["date"], 
        y=df[f"{prefix}_usage_cost"], 
        name="Notkun", 
        marker_color=color,
        customdata=hover_data,  # Pass total cost and formatted date for hover
        hovertemplate=hovertemplate
    ))
    
    return fig

def add_traffic_light_background(fig, y_max, is_electricity=True):
    """Add traffic light background zones to a chart"""
    # Set colors based on chart type
    title_color = COLORS["red"] if is_electricity else COLORS["dark_blue"]
    
    # Add colored background rectangles (traffic light zones)
    green_max = 0.55
    yellow_max = 0.8

    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=1, y1=y_max * green_max,
        xref="paper", yref="y",
        fillcolor=COLORS["light_green_bg"],
        line_width=0,
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=0, y0=y_max * green_max, x1=1, y1=y_max * yellow_max,
        xref="paper", yref="y",
        fillcolor=COLORS["light_yellow_bg"],
        line_width=0,
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=0, y0=y_max * yellow_max, x1=1, y1=y_max,
        xref="paper", yref="y",
        fillcolor=COLORS["light_red_bg"],
        line_width=0,
        layer="below"
    )
    
    # Update layout with common settings
    fig.update_layout(
        paper_bgcolor="rgba(255,255,255,0.2)",
        # title_font_color=title_color,
        # legend_title_font_color=COLORS["dark_gray"],
        # legend_title="Kostnaðarliðir",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def add_average_lines(fig, df, prefix, y_max):
    """Add average comparison lines to a chart"""
    # Calculate average for the period
    avg = df[f"{prefix}_total"].mean()
    
    # Add average lines (simulated comparisons)
    # Neighborhood average (slightly higher than user)
    neighborhood_avg = avg * 1.15
    
    # Home type average (slightly lower than user)
    home_type_avg = avg * 0.9
    
    # Add average line for neighborhood
    fig.add_trace(go.Scatter(
        x=[df["date"].min(), df["date"].max()],
        y=[neighborhood_avg, neighborhood_avg],
        mode="lines",
        name="Meðaltal hverfis",
        line=dict(color=COLORS["mid_gray"], width=2, dash="dashdot"),
    ))
    
    # Add average line for home type
    fig.add_trace(go.Scatter(
        x=[df["date"].min(), df["date"].max()],
        y=[home_type_avg, home_type_avg],
        mode="lines",
        name="Meðaltal húsgerðar",
        line=dict(color=COLORS["yellow"], width=2, dash="dash"),
    ))
    
    return fig, avg, neighborhood_avg, home_type_avg

def create_electricity_chart(df):
    """Create the electricity cost chart"""
    # Create figure
    fig_cost_elec = go.Figure()
    
    # Calculate y-axis range for traffic light background
    y_max = max(df["elec_total"].max() * 1.1, 1)  # Add 10% padding
    
    # Create traffic light background
    fig_cost_elec.update_layout(
        barmode="stack",
        title="Rafmagn – Daglegur kostnaður (kr.)",
        xaxis_title="Dagsetning",
        yaxis_title="kr.",
        paper_bgcolor="rgba(255,255,255,0.5)",
        title_font_color=COLORS["red"],
        # legend_title_font_color=COLORS["dark_gray"],
        # legend_title="Kostnaðarliðir",
        yaxis=dict(range=[0, y_max]),
        height=500,
    )
    
    # Add traffic light background
    fig_cost_elec = add_traffic_light_background(fig_cost_elec, y_max, is_electricity=True)
    
    # Add cost bars
    fig_cost_elec = add_cost_bars(fig_cost_elec, df, "elec")
    
    # Add average lines
    fig_cost_elec, avg_cost, neighborhood_avg, home_type_avg = add_average_lines(
        fig_cost_elec, df, "elec", y_max
    )
    
    return fig_cost_elec, avg_cost, neighborhood_avg, home_type_avg

def create_water_chart(df):
    """Create the hot water cost chart"""
    # Create figure
    fig_cost_water = go.Figure()
    
    # Calculate y-axis range for traffic light background
    y_max = max(df["water_total"].max() * 1.1, 1)  # Add 10% padding
    
    # Create traffic light background
    fig_cost_water.update_layout(
        barmode="stack",
        title="Heitt vatn – Daglegur kostnaður (kr.)",
        xaxis_title="Dagsetning",
        yaxis_title="kr.",
        paper_bgcolor="rgba(255,255,255,0.5)",
        title_font_color=COLORS["dark_blue"],
        # legend_title_font_color=COLORS["dark_gray"],
        # legend_title="Kostnaðarliðir",
        # yaxis=dict(range=[0, y_max]),
        height=500,
    )
    
    # Add traffic light background
    fig_cost_water = add_traffic_light_background(fig_cost_water, y_max, is_electricity=False)
    
    # Add cost bars
    fig_cost_water = add_cost_bars(fig_cost_water, df, "water")
    
    # Add average lines
    fig_cost_water, avg_cost, neighborhood_avg, home_type_avg = add_average_lines(
        fig_cost_water, df, "water", y_max
    )
    
    return fig_cost_water, avg_cost, neighborhood_avg, home_type_avg

def display_comparison_metrics(avg_cost, neighborhood_avg, home_type_avg, is_electricity=True, df=None):
    """Display comparison metrics below the chart"""
    # Set color based on chart type
    title_color = COLORS["red"] if is_electricity else COLORS["dark_blue"]
    
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    
    # Get the prefix based on chart type
    prefix = "elec" if is_electricity else "water"
    
    # Calculate total cost for the period - only sum the days displayed in the chart
    # The df passed to this function is already aggregated based on the selected time grain
    if df is not None:
        # Sum the total costs directly from the dataframe
        total_period_cost = df[f"{prefix}_total"].sum()
    else:
        # Fallback: calculate from the average
        # Estimate number of days (30 is a reasonable default)
        days = 30
        total_period_cost = float(avg_cost) * days
    
    # Total cost for the period
    with col1:
        st.metric(
            "Heildarkostnaður á tímabili",
            f"{total_period_cost:,.0f} kr."
        )
    
    # Comparison with neighborhood average
    with col2:
        # Calculate average cost per day for comparison
        avg_daily_cost = float(avg_cost.mean()) if hasattr(avg_cost, 'mean') else float(avg_cost)
        diff_pct = ((avg_daily_cost / neighborhood_avg) - 1) * 100
        # Format the percentage with the arrow inline and color
        if diff_pct > 0:
            sign = "+"
            arrow = "↑"
            color = COLORS["red"]  # Higher cost is bad (red)
        else:
            sign = "-"
            arrow = "↓"
            color = COLORS["green"]  # Lower cost is good (green)
        
        # Use st.metric to match the style of "Heildarkostnaður á tímabili"
        st.metric(
            "Samanborið við hverfi",
            f"{sign}{abs(diff_pct):.1f}% {arrow}",
        )
    
    # Comparison with home type average
    with col3:
        # Calculate average cost per day for comparison
        avg_daily_cost = float(avg_cost.mean()) if hasattr(avg_cost, 'mean') else float(avg_cost)
        diff_pct = ((avg_daily_cost / home_type_avg) - 1) * 100
        # Format the percentage with the arrow inline and color
        if diff_pct > 0:
            sign = "+"
            arrow = "↑"
            color = COLORS["red"]  # Higher cost is bad (red)
        else:
            sign = "-"
            arrow = "↓"
            color = COLORS["green"]  # Lower cost is good (green)
        
        # Use st.metric to match the style of "Heildarkostnaður á tímabili"
        st.metric(
            "Samanborið við húsgerð",
            f"{sign}{abs(diff_pct):.1f}% {arrow}"
        )

def display_time_grain_selector(chart_type="electricity"):
    """Display time grain radio buttons and handle selection
    
    Args:
        chart_type: Type of chart ("electricity" or "water") to create unique key
    """
    # Radio buttons for time grain selection
    time_grain_options = {
        "daily": "Daglegt",
        "weekly": "Vikulegt",
        "monthly": "Mánaðarlegt"
    }
    
    # Create a unique key for each chart type
    radio_key = f"time_grain_radio_{chart_type}"
    
    selected_time_grain = st.radio(
        "",
        options=list(time_grain_options.keys()),
        format_func=lambda x: time_grain_options[x],
        index=list(time_grain_options.keys()).index(st.session_state.time_grain),
        horizontal=True,
        key=radio_key
    )
    
    # Update session state if selection changed
    if selected_time_grain != st.session_state.time_grain:
        st.session_state.time_grain = selected_time_grain
        st.rerun()

def display_electricity_chart(df):
    """Display electricity chart and metrics"""
    # Display time grain selector above chart with electricity chart type
    display_time_grain_selector(chart_type="electricity")
    
    # Create chart
    fig_cost_elec, avg_cost, neighborhood_avg, home_type_avg = create_electricity_chart(df)
    
    # Display chart
    st.plotly_chart(fig_cost_elec, use_container_width=True)
    
    # Display comparison metrics
    display_comparison_metrics(avg_cost, neighborhood_avg, home_type_avg, is_electricity=True, df=df)

def display_water_chart(df):
    """Display hot water chart and metrics"""
    # Display time grain selector above chart with water chart type
    display_time_grain_selector(chart_type="water")
    
    # Create chart
    fig_cost_water, avg_cost, neighborhood_avg, home_type_avg = create_water_chart(df)
    
    # Display chart
    st.plotly_chart(fig_cost_water, use_container_width=True)
    
    # Display comparison metrics
    display_comparison_metrics(avg_cost, neighborhood_avg, home_type_avg, is_electricity=False, df=df)
