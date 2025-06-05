import pandas as pd
import numpy as np
import streamlit as st
from datetime import date, timedelta
import random

# Set fixed seeds for reproducibility
np.random.seed(42)
random.seed(42)

# --- Icelandic localization ---
ICELANDIC_MONTHS = {
    1: "janúar", 2: "febrúar", 3: "mars", 4: "apríl",
    5: "maí", 6: "júní", 7: "júlí", 8: "ágúst",
    9: "september", 10: "október", 11: "nóvember", 12: "desember"
}

ICELANDIC_MONTHS_SHORT = {
    1: "jan", 2: "feb", 3: "mar", 4: "apr",
    5: "maí", 6: "jún", 7: "júl", 8: "ágú",
    9: "sep", 10: "okt", 11: "nóv", 12: "des"
}

def get_icelandic_month(month_num):
    return ICELANDIC_MONTHS.get(month_num, "")

def format_date_icelandic(d):
    month_name = get_icelandic_month(d.month)
    return f"{month_name} {d.year}"

# --- Brand Colors ---
COLORS = {
    "red": "#58d66b",
    "mid_red": "#D84A4B",
    "green": "#58d66b", #8CD022",
    "light_blue": "#4CD0DC",
    "dark_blue": "#9958d6",
    "dark_gray": "#323232",
    "light_gray": "#E8EFEF",
    "mid_gray": "#8FA9AF",
    "mid_light_gray": "#C9D6D9",
    "blue_gray": "#9958d6",
    "dark_blue_gray": "#364C4E",
    "yellow": "#F6D51C",
    "light_yellow": "#FADF62",
    # Light chart background colors
    "light_red_bg": "rgba(255, 200, 200, 0.3)",
    "light_yellow_bg": "rgba(255, 235, 150, 0.3)",
    "light_green_bg": "rgba(180, 240, 180, 0.3)"
}

# --- Constants ---
DAILY_FIXED_COST = 100
MONTHLY_EQUALIZATION = 200
ELECTRICITY_UNIT_COST = 7
HOT_WATER_UNIT_COST = 150  # Increased from 20 to make usage cost higher than tax
TAX_RATE = 0.10

# Fixed daily adjustments for user preferences
EV_DAILY_KWH = 10.0  # 10 kWh per day for EV
ELECTRIC_HOT_TUB_DAILY_KWH = 8.0  # 8 kWh per day for electric hot tub
GEOTHERMAL_HOT_TUB_DAILY_M3 = 0.2  # 0.2 m³ per day for geothermal hot tub
HEAT_PUMP_ELEC_REDUCTION_KWH = 3.0  # 3 kWh per day reduction with heat pump
HEAT_PUMP_WATER_REDUCTION_M3 = 0.05  # 0.05 m³ per day reduction with heat pump

# Energy usage categories (kWh per day)
# Values adjusted to sum to 8795 when accumulated over the period
ENERGY_CATEGORIES = {
    "energy_ev": 266.0,  # Electric vehicle (30.3% of total)
    "energy_hot_tub": 213.0,  # Electric hot tub (24.2% of total)
    "energy_refrigerator": 40.0,  # Refrigerator (4.5% of total)
    "energy_freezer": 53.0,  # Freezer (6.1% of total)
    "energy_cooker": 32.0,  # Electric cooker (3.6% of total)
    "energy_dishwasher": 26.0,  # Dishwasher (3.0% of total)
    "energy_washing_machine": 21.0,  # Washing machine (2.4% of total)
    "energy_dryer": 66.0,  # Clothes dryer (7.6% of total)
    "energy_lighting": 26.0,  # Lighting (3.0% of total)
    "energy_heating": 80.0,  # Electric heating (9.1% of total)
    "energy_other": 53.0,  # Other appliances (6.0% of total)
    # Total: 8795.0 kWh (100%)
}

# Hot water usage categories (m³ per day)
# Values adjusted to sum to 600 when accumulated over the period
WATER_CATEGORIES = {
    "water_hot_tub": 180.0,  # Hot tub (30.0% of total)
    "water_shower": 150.0,  # Shower (25.0% of total)
    "water_radiators": 120.0,  # Radiators/heating (20.0% of total)
    "water_faucets": 60.0,  # Faucets/taps (10.0% of total)
    "water_dishwasher": 30.0,  # Dishwasher (5.0% of total)
    "water_washing_machine": 24.0,  # Washing machine (4.0% of total)
    "water_floor_heating": 36.0,  # Floor heating (6.0% of total)
    # Total: 600.0 m³ (100%)
}

# --- Data generation and processing ---
def generate_data(start_date, end_date):
    """Generate sample data for the given date range"""
    # Create date range
    date_range = pd.date_range(start=start_date, end=end_date)
    date_key = f"{start_date}_{end_date}"
    
    # Create dataframe with dates
    df = pd.DataFrame({"date": date_range})
    
    # Add seasonal variations
    # Higher in winter, lower in summer
    df["month"] = df["date"].dt.month
    winter_elec_factor = np.where(df["month"].isin([12, 1, 2]), 1.5, 1.0)
    fall_spring_elec_factor = np.where(df["month"].isin([3, 4, 10, 11]), 1.2, 1.0)
    winter_water_factor = np.where(df["month"].isin([12, 1, 2]), 1.3, 1.0)
    fall_spring_water_factor = np.where(df["month"].isin([3, 4, 10, 11]), 1.1, 1.0)
    
    # Get user preferences from session state
    has_hot_tub = st.session_state.get('has_hot_tub', False)
    hot_tub_type = st.session_state.get('hot_tub_type', 'geothermal') if has_hot_tub else None
    has_ev = st.session_state.get('has_ev', False)
    has_heat_pump = st.session_state.get('has_heat_pump', False)
    
    # Store base values in session state to avoid re-randomizing when toggles change
    # Only generate new random values if date range changes or if base values don't exist
    if 'base_data' not in st.session_state or st.session_state.get('date_key', '') != date_key:
        # Base electricity usage (kWh)
        base_elec = np.random.normal(15, 3, len(df)) * winter_elec_factor * fall_spring_elec_factor
        
        # Base hot water usage (m3) - reduced since we increased the unit cost
        base_water = np.random.normal(0.3, 0.05, len(df)) * winter_water_factor * fall_spring_water_factor
        
        # Store in session state
        st.session_state['base_data'] = {
            'base_elec': base_elec,
            'base_water': base_water
        }
        st.session_state['date_key'] = date_key
    else:
        # Use stored values
        base_elec = st.session_state['base_data']['base_elec']
        base_water = st.session_state['base_data']['base_water']
    
    # Apply fixed daily adjustments based on user preferences
    ev_usage = np.ones(len(df)) * EV_DAILY_KWH if has_ev else 0
    electric_hot_tub_usage = np.ones(len(df)) * ELECTRIC_HOT_TUB_DAILY_KWH if has_hot_tub and hot_tub_type == 'electric' else 0
    geothermal_hot_tub_usage = np.ones(len(df)) * GEOTHERMAL_HOT_TUB_DAILY_M3 if has_hot_tub and hot_tub_type == 'geothermal' else 0
    elec_reduction = np.ones(len(df)) * HEAT_PUMP_ELEC_REDUCTION_KWH if has_heat_pump else 0
    water_reduction = np.ones(len(df)) * HEAT_PUMP_WATER_REDUCTION_M3 if has_heat_pump else 0
    
    # Add energy usage categories
    # EV and hot tub are conditional on user preferences
    # Calculate daily values by dividing the total by the number of days in the period
    days_in_period = len(df)
    
    # Handle EV and hot tub based on user preferences
    if has_ev:
        df["energy_ev"] = ENERGY_CATEGORIES["energy_ev"] / days_in_period * np.random.uniform(0.8, 1.2, len(df))
    else:
        df["energy_ev"] = 0
        
    if has_hot_tub and hot_tub_type == 'electric':
        df["energy_hot_tub"] = ENERGY_CATEGORIES["energy_hot_tub"] / days_in_period * np.random.uniform(0.8, 1.2, len(df))
    else:
        df["energy_hot_tub"] = 0
    
    # Add random variation to each category (±20%)
    for category, total_value in ENERGY_CATEGORIES.items():
        # Skip EV and hot tub as they're already handled
        if category in ["energy_ev", "energy_hot_tub"]:
            continue
            
        # Calculate daily base value
        daily_base = total_value / days_in_period
        
        # Apply seasonal factors to some categories
        seasonal_factor = 1.0
        if category == "energy_heating":
            # More heating in winter
            seasonal_factor = winter_elec_factor * fall_spring_elec_factor
        elif category == "energy_refrigerator" or category == "energy_freezer":
            # Slightly more in summer (warmer ambient temperature)
            summer_factor = np.where(df["month"].isin([6, 7, 8]), 1.2, 1.0)
            seasonal_factor = summer_factor
            
        # Generate random variations around the base value
        variation = np.random.uniform(0.8, 1.2, len(df))
        df[category] = daily_base * variation * seasonal_factor
        
    # Normalize the values to ensure they sum exactly to the target total
    energy_cols = [col for col in df.columns if col.startswith('energy_')]
    total_energy = sum(ENERGY_CATEGORIES.values())
    current_sum = df[energy_cols].sum().sum()
    
    # Apply scaling factor to make the sum match the target
    if current_sum > 0:  # Avoid division by zero
        scaling_factor = total_energy / current_sum
        for col in energy_cols:
            df[col] = df[col] * scaling_factor
    
    # Calculate final electricity usage as sum of all energy categories
    df["elec_usage"] = base_elec - elec_reduction
    for category in ENERGY_CATEGORIES.keys():
        df["elec_usage"] += df[category]
    
    # Ensure usage is never negative
    df["elec_usage"] = df["elec_usage"].clip(lower=0)
    
    # Calculate final hot water usage
    df["water_usage"] = base_water + geothermal_hot_tub_usage - water_reduction
    # Ensure usage is never negative
    df["water_usage"] = df["water_usage"].clip(lower=0)
    
    # Add fixed costs (divided by days in month to get daily values)
    days_in_month = pd.Series(df["date"].dt.daysinmonth)
    df["cost_fixed"] = DAILY_FIXED_COST
    df["cost_equalization"] = MONTHLY_EQUALIZATION / days_in_month
    
    # Calculate costs
    df = compute_cost_columns(df, "elec_usage", ELECTRICITY_UNIT_COST, "elec")
    df = compute_cost_columns(df, "water_usage", HOT_WATER_UNIT_COST, "water")
    
    return df

def compute_cost_columns(df, usage_col, unit_price, prefix):
    """Calculate cost components for a given usage column"""
    # Use the actual column name from the dataframe
    usage = df[usage_col] * unit_price
    tax = usage * TAX_RATE
    df[f"{prefix}_usage_cost"] = usage  # Renamed to avoid confusion with usage quantity
    df[f"{prefix}_tax"] = tax
    df[f"{prefix}_total"] = df["cost_fixed"] + df["cost_equalization"] + usage + tax
    return df

def aggregate_by_time_period(df, period):
    """Aggregate data by specified time period (daily, weekly, monthly)"""
    # Make a copy to avoid modifying the original
    agg_df = df.copy()
    
    # Get all energy category columns
    energy_cols = [col for col in df.columns if col.startswith('energy_')]
    
    if period == "daily":
        # Daily data is already at the right grain
        return agg_df
    elif period == "weekly":
        # Add week number
        agg_df["year"] = agg_df["date"].dt.isocalendar().year
        agg_df["week"] = agg_df["date"].dt.isocalendar().week
        
        # Group by year and week
        agg_dict = {
            "date": "first",  # Use first date of the week
            "elec_usage": "sum",
            "water_usage": "sum",
            "cost_fixed": "sum",
            "cost_equalization": "sum",
            "elec_usage_cost": "sum",
            "elec_tax": "sum",
            "elec_total": "sum",
            "water_usage_cost": "sum",
            "water_tax": "sum",
            "water_total": "sum"
        }
        
        # Add energy category columns to aggregation
        for col in energy_cols:
            agg_dict[col] = "sum"
            
        grouped = agg_df.groupby(["year", "week"]).agg(agg_dict).reset_index()
        
    elif period == "monthly":
        # Add year and month
        agg_df["year"] = agg_df["date"].dt.year
        agg_df["month"] = agg_df["date"].dt.month
        
        # Group by year and month
        agg_dict = {
            "date": "first",  # Use first date of the month
            "elec_usage": "sum",
            "water_usage": "sum",
            "cost_fixed": "sum",
            "cost_equalization": "sum",
            "elec_usage_cost": "sum",
            "elec_tax": "sum",
            "elec_total": "sum",
            "water_usage_cost": "sum",
            "water_tax": "sum",
            "water_total": "sum"
        }
        
        # Add energy category columns to aggregation
        for col in energy_cols:
            agg_dict[col] = "sum"
            
        grouped = agg_df.groupby(["year", "month"]).agg(agg_dict).reset_index()
        
        # Set date to first day of month for proper display
        grouped["date"] = grouped.apply(lambda row: pd.Timestamp(year=int(row["year"]), month=int(row["month"]), day=1), axis=1)
    
    return grouped

def get_monthly_costs(df):
    """Calculate monthly cost summaries"""
    # Group by year and month
    monthly = df.copy()
    monthly["year"] = monthly["date"].dt.year
    monthly["month"] = monthly["date"].dt.month
    
    # Sum costs by month
    monthly_costs = monthly.groupby(["year", "month"]).agg({
        "elec_total": "sum",
        "water_total": "sum"
    }).reset_index()
    
    # Add total cost
    monthly_costs["total"] = monthly_costs["elec_total"] + monthly_costs["water_total"]
    
    # Add month name
    monthly_costs["month_name"] = monthly_costs["month"].apply(get_icelandic_month)
    
    # Sort by date
    monthly_costs = monthly_costs.sort_values(["year", "month"])
    
    return monthly_costs

def get_last_full_month():
    """Get the last full month (previous month)"""
    today = date.today()
    if today.month == 1:
        return date(today.year - 1, 12, 1)
    else:
        return date(today.year, today.month - 1, 1)

def get_current_month_costs(df):
    """Get costs for the current month"""
    today = date.today()
    current_month_data = df[
        (df["date"].dt.year == today.year) & 
        (df["date"].dt.month == today.month)
    ]
    
    if len(current_month_data) == 0:
        return 0, 0, 0
    
    elec_cost = current_month_data["elec_total"].sum()
    water_cost = current_month_data["water_total"].sum()
    total_cost = elec_cost + water_cost
    
    return total_cost, elec_cost, water_cost

def generate_last_month_data():
    """Generate data specifically for the last full month"""
    # Get last month's date range
    last_month = get_last_full_month()
    
    # Create date range for the entire month
    if last_month.month == 12:
        next_month = date(last_month.year + 1, 1, 1)
    else:
        next_month = date(last_month.year, last_month.month + 1, 1)
    
    # Generate start and end dates for the full month
    start_date = date(last_month.year, last_month.month, 1)
    end_date = next_month - timedelta(days=1)
    
    # Generate data for the full month
    return generate_data(start_date, end_date)

def get_last_month_costs(df=None):
    """Get costs for the last full month"""
    # If no dataframe is provided, generate data specifically for the last month
    if df is None:
        df = generate_last_month_data()
    
    last_month = get_last_full_month()
    last_month_data = df[
        (df["date"].dt.year == last_month.year) & 
        (df["date"].dt.month == last_month.month)
    ]
    
    if len(last_month_data) == 0:
        return 0, 0, 0
    
    elec_cost = last_month_data["elec_total"].sum()
    water_cost = last_month_data["water_total"].sum()
    total_cost = elec_cost + water_cost
    
    return total_cost, elec_cost, water_cost

def get_previous_month_costs(df):
    """Get costs for the month before last month"""
    if df is None:
        # Fallback values if no data is provided
        return 11500, 7500, 4000
    
    today = date.today()
    last_month = today.replace(day=1) - timedelta(days=1)
    previous_month_end = date(last_month.year, last_month.month, 1) - timedelta(days=1)
    previous_month_start = date(previous_month_end.year, previous_month_end.month, 1)
    
    # Filter data for the month before last month
    previous_month_data = df[(df['date'] >= pd.Timestamp(previous_month_start)) & 
                            (df['date'] <= pd.Timestamp(previous_month_end))]
    
    if len(previous_month_data) > 0:
        previous_month_elec = previous_month_data["elec_total"].sum()
        previous_month_water = previous_month_data["water_total"].sum()
        previous_month_total = previous_month_elec + previous_month_water
        return previous_month_total, previous_month_elec, previous_month_water
    else:
        # Fallback values
        return 11500, 7500, 4000

def get_month_to_date_costs(df, year, month, day_of_month):
    """Get costs for a specific month up to a specific day"""
    month_to_date_data = df[
        (df["date"].dt.year == year) & 
        (df["date"].dt.month == month) &
        (df["date"].dt.day <= day_of_month)
    ]
    
    if len(month_to_date_data) == 0:
        return 0, 0, 0
    
    elec_cost = month_to_date_data["elec_total"].sum()
    water_cost = month_to_date_data["water_total"].sum()
    total_cost = elec_cost + water_cost
    
    return total_cost, elec_cost, water_cost

def calculate_monthly_costs(df):
    """Calculate costs by month without deltas"""
    # Group by year and month
    monthly = df.copy()
    monthly["year"] = monthly["date"].dt.year
    monthly["month"] = monthly["date"].dt.month
    
    # Sum costs by month
    monthly_costs = monthly.groupby(["year", "month"]).agg({
        "elec_total": "sum",
        "water_total": "sum"
    }).reset_index()
    
    # Add total cost
    monthly_costs["total"] = monthly_costs["elec_total"] + monthly_costs["water_total"]
    
    # Add month name
    monthly_costs["month_name"] = monthly_costs["month"].apply(get_icelandic_month)
    
    # Sort by date
    monthly_costs = monthly_costs.sort_values(["year", "month"])
    
    return monthly_costs

# Removed month comparison calculation functions
