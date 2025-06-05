import streamlit as st
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from utils import (
    format_date_icelandic,
    get_last_full_month,
    get_current_month_costs,
    get_last_month_costs,
    get_monthly_costs,
    calculate_monthly_costs
)

# Date inputs moved to main page

def on_hot_tub_change():
    """Callback when hot tub toggle changes"""
    # Update session state from the toggle key
    st.session_state.has_hot_tub = st.session_state.hot_tub_toggle
    # Force rerun to update data immediately
    st.session_state.force_rerun = True

def on_hot_tub_type_change():
    """Callback when hot tub type changes"""
    # Update session state based on selection
    selection = st.session_state.hot_tub_type_radio
    st.session_state.hot_tub_type = "geothermal" if selection == "Hitaveita" else "electric"
    # Force rerun to update data immediately
    st.session_state.force_rerun = True

def on_ev_change():
    """Callback when EV toggle changes"""
    # Update session state from the toggle key
    st.session_state.has_ev = st.session_state.ev_toggle
    # Force rerun to update data immediately
    st.session_state.force_rerun = True

def on_heat_pump_change():
    """Callback when heat pump toggle changes"""
    # Update session state from the toggle key
    st.session_state.has_heat_pump = st.session_state.heat_pump_toggle
    # Force rerun to update data immediately
    st.session_state.force_rerun = True

def display_user_preferences():
    """Display user preference toggles in the sidebar"""
    st.sidebar.title("Viltu bæta við:")
    
    # Initialize session state for user preferences if not already set
    if 'has_hot_tub' not in st.session_state:
        st.session_state.has_hot_tub = False
    if 'hot_tub_type' not in st.session_state:
        st.session_state.hot_tub_type = "geothermal"
    if 'has_ev' not in st.session_state:
        st.session_state.has_ev = False
    if 'has_heat_pump' not in st.session_state:
        st.session_state.has_heat_pump = False
    if 'force_rerun' not in st.session_state:
        st.session_state.force_rerun = False
    
    # Add toggle for hot tub with callback
    st.sidebar.toggle(
        "Heitur pottur", 
        value=st.session_state.has_hot_tub, 
        key="hot_tub_toggle", 
        on_change=on_hot_tub_change
    )
    
    # If hot tub is selected, show radio buttons for type
    if st.session_state.has_hot_tub:
        st.sidebar.radio(
            "Tegund potts:",
            options=["Hitaveita", "Rafmagn"],
            index=0 if st.session_state.hot_tub_type == "geothermal" else 1,
            horizontal=True,
            key="hot_tub_type_radio",
            on_change=on_hot_tub_type_change
        )
    
    # Add other toggles with callbacks
    st.sidebar.toggle(
        "Rafbíll", 
        value=st.session_state.has_ev, 
        key="ev_toggle", 
        on_change=on_ev_change
    )
    
    st.sidebar.toggle(
        "Varmadæla", 
        value=st.session_state.has_heat_pump, 
        key="heat_pump_toggle", 
        on_change=on_heat_pump_change
    )
    
    # Add separator before monthly breakdown
    st.sidebar.markdown("---")

def calculate_percentage_change(current, previous):
    """Calculate percentage change between two values"""
    if previous == 0:
        return 0  # Avoid division by zero
    return ((current / previous) - 1) * 100

def format_percentage_change(percentage):
    """Format percentage change with arrow and color"""
    if percentage > 0:
        return f"<span style='color:#BE2425'>↑ {abs(percentage):.1f}%</span>"
    elif percentage < 0:
        return f"<span style='color:#0E8CA6'>↓ {abs(percentage):.1f}%</span>"
    else:
        return "0%"

def display_current_and_last_month_costs(df):
    """Display current and last month costs in the sidebar"""
    st.sidebar.title("Kostnaður")
    
    # Get last month's costs
    last_month = get_last_full_month()
    last_month_name = format_date_icelandic(last_month)
    
    # Get costs for last month - use the provided df for consistency with the main chart
    # Filter the dataframe to only include last month's data
    last_month_data = df[
        (df["date"].dt.year == last_month.year) & 
        (df["date"].dt.month == last_month.month)
    ]
    
    if len(last_month_data) > 0:
        last_month_elec = last_month_data["elec_total"].sum()
        last_month_water = last_month_data["water_total"].sum()
        last_month_total = last_month_elec + last_month_water
    else:
        # Fallback if no data for last month in the filtered dataframe
        last_month_total, last_month_elec, last_month_water = get_last_month_costs(None)
    
    # Display last month costs
    st.sidebar.header(f"{last_month_name.title()}")
    
    # Display total cost
    st.sidebar.markdown(
        f"<h2>{last_month_total:,.0f} kr.</h2>", 
        unsafe_allow_html=True
    )
    
    # Display electricity cost
    st.sidebar.markdown(
        f"**Rafmagn:** {last_month_elec:,.0f} kr.", 
        unsafe_allow_html=True
    )
    
    # Display water cost
    st.sidebar.markdown(
        f"**Heitt vatn:** {last_month_water:,.0f} kr.", 
        unsafe_allow_html=True
    )
    
    # Get current month costs
    current_month = date.today()
    current_month_name = format_date_icelandic(current_month)
    current_month_total, current_month_elec, current_month_water = get_current_month_costs(df)
    
    # Display current month costs
    st.sidebar.header(f"{current_month_name.title()} (það sem af er)")

    # Display total cost
    st.sidebar.markdown(
        f"<h3>{current_month_total:,.0f} kr.</h3>", 
        unsafe_allow_html=True
    )
    
    # Display electricity cost
    st.sidebar.markdown(
        f"**Rafmagn:** {current_month_elec:,.0f} kr.", 
        unsafe_allow_html=True
    )
    
    # Display water cost
    st.sidebar.markdown(
        f"**Heitt vatn:** {current_month_water:,.0f} kr.", 
        unsafe_allow_html=True
    )
    
    # Add separator before monthly breakdown
    st.sidebar.markdown("---")

def display_monthly_cost_overview(df):
    """Display monthly cost breakdown in the sidebar"""
    st.sidebar.subheader("Mánaðarleg sundurliðun")
    
    # Get monthly costs
    monthly_costs = calculate_monthly_costs(df)
    
    # Sort monthly costs by year and month in descending order
    sorted_costs = monthly_costs.sort_values(["year", "month"], ascending=False)
    
    # Create a dictionary to store previous month's data for comparison
    previous_data = {}
    
    # Display monthly costs
    for i, (_, row) in enumerate(sorted_costs.iterrows()):
        month_year = f"{row['month_name']} {row['year']}"
        total = row['total']
        elec = row['elec_total']
        water = row['water_total']
        
        # Get previous month's data for comparison (if available)
        if i < len(sorted_costs) - 1:
            prev_row = sorted_costs.iloc[i + 1]
            prev_total = prev_row['total']
            prev_elec = prev_row['elec_total']
            prev_water = prev_row['water_total']
            
            # Calculate percentage changes
            total_change_pct = calculate_percentage_change(total, prev_total)
            elec_change_pct = calculate_percentage_change(elec, prev_elec)
            water_change_pct = calculate_percentage_change(water, prev_water)
            
            # Format percentage changes
            total_change_formatted = format_percentage_change(total_change_pct)
            elec_change_formatted = format_percentage_change(elec_change_pct)
            water_change_formatted = format_percentage_change(water_change_pct)
        else:
            # No previous month data available
            total_change_formatted = ""
            elec_change_formatted = ""
            water_change_formatted = ""
        
        # Use HTML for better formatting and smaller font
        st.sidebar.markdown(f"""
        <div style='border-bottom: 1px solid #eee; padding-bottom: 8px; margin-bottom: 8px;'>
            <div style='font-weight: bold;'>{month_year}</div>
            <div style='font-size: 14px;'>Heildarkostnaður: {total:,.0f} kr. {total_change_formatted}</div>
            <div style='font-size: 12px; color: #666;'>
                Rafmagn: {elec:,.0f} kr. {elec_change_formatted}<br>
                Heitt vatn: {water:,.0f} kr. {water_change_formatted}
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_sidebar(df):
    """Display all cost and user preference information in the sidebar"""
    # display_current_and_last_month_costs(df)
    display_user_preferences()
    display_monthly_cost_overview(df)
