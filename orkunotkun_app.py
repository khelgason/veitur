import streamlit as st
from datetime import date, timedelta
import plotly.graph_objects as go

# Import from our utility modules
from utils import generate_data, aggregate_by_time_period, COLORS, get_last_full_month
from charts import *
from sidebar import display_sidebar

def main():
    """Main app function"""
    st.set_page_config(page_title="Orkunotkun", layout="wide")
    
    # Check if we need to rerun the app due to preference changes
    if 'force_rerun' in st.session_state and st.session_state.force_rerun:
        # Reset the flag and rerun
        st.session_state.force_rerun = False
        st.rerun()
    
    # Add logo to the sidebar
    st.logo("Veitur-logo/VEITUR_Merki_02.png", size="large", link=None, icon_image="Veitur-logo/VEITUR_Merki_01.png")
    
    # Display the title in the main area
    st.title("Orkuvitund")
    
    # Date inputs in main page - using 4 columns with date pickers in the middle two
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        # Set start date to first day of last month
        last_month = get_last_full_month()
        start_date = st.date_input("Frá:", date(last_month.year, last_month.month, 1), max_value="today")
    with col2:
        end_date = st.date_input("Til:", date.today(), max_value="today")
    
    if start_date > end_date:
        st.error("Upphafsdagur má ekki vera eftir lokadag.")
        return
    
    # Generate data - this is the original daily data
    df = generate_data(start_date, end_date)
    
    # Display sidebar with costs and user preferences
    display_sidebar(df)
    
    # Initialize session state for time grain if not exists
    if 'time_grain' not in st.session_state:
        st.session_state.time_grain = "daily"
    
    # Create tabs for chart selection
    tab1, tab2, tab3 = st.tabs(["Í hvað er orkan að fara", "Rafmagnskostnaður", "Heitavatnkostnaður"])
    
    # Aggregate data based on selected time grain for charts only
    # The sidebar will continue to use the original daily data
    aggregated_df = aggregate_by_time_period(df, st.session_state.time_grain)
    
    # Display charts in their respective tabs
    with tab2:
        display_electricity_chart(aggregated_df)
        
    with tab3:
        display_water_chart(aggregated_df)

    # Energy usage breakdown (both electricity and hot water)
    with tab1:
        display_energy_breakdown_chart(aggregated_df)

if __name__ == "__main__":
    main()
