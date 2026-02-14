"""
Interactive Market Data Charting Application

A modern web-based financial charting application with interactive candlestick charts,
customizable technical indicators, and an extensible plugin system.

Author: Market Data Team
Version: 2.0.0
"""

import streamlit as st
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime

from src.data_manager import DataManager
from src.chart_engine import InteractiveChartEngine
from src.plugin_manager import PluginManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Interactive Market Data Charting",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = None

if 'chart_engine' not in st.session_state:
    st.session_state.chart_engine = None

if 'plugin_manager' not in st.session_state:
    st.session_state.plugin_manager = None


@st.cache_resource
def initialize_application():
    """Initialize the application components."""
    try:
        # Initialize DataManager
        db_path = Path("market_data.db")
        if not db_path.exists():
            st.error(f"Database not found: {db_path}")
            st.info("Please ensure market_data.db exists in the project root directory.")
            return None, None, None
        
        data_manager = DataManager(str(db_path))
        
        # Initialize PluginManager
        plugins_dir = Path("plugins/indicators")
        plugin_manager = PluginManager(str(plugins_dir))
        
        # Load plugins
        results = plugin_manager.load_all_plugins()
        loaded_count = sum(1 for success, _ in results.values() if success)
        logger.info(f"Loaded {loaded_count}/{len(results)} plugins")
        
        # Initialize ChartEngine
        chart_engine = InteractiveChartEngine(
            data_manager=data_manager,
            plugin_manager=plugin_manager
        )
        
        return data_manager, chart_engine, plugin_manager
    
    except Exception as e:
        logger.error(f"Error initializing application: {e}")
        st.error(f"Failed to initialize application: {e}")
        return None, None, None


def render_sidebar():
    """Render the sidebar controls."""
    st.sidebar.title("📊 Chart Settings")
    
    # Application info
    with st.sidebar.expander("ℹ️ About", expanded=False):
        st.write("""
        **Interactive Market Data Charting v2.0.0**
        
        A modern financial charting application with:
        - Interactive candlestick charts
        - Multiple time frame support
        - Technical indicators
        - Custom plugin system
        
        Built with Streamlit and Plotly
        """)
    
    # Data source section
    st.sidebar.subheader("Data Source")
    
    if st.session_state.data_manager:
        available_tickers = st.session_state.data_manager.get_available_tickers()
        
        if not available_tickers:
            st.sidebar.warning("No tickers found in database")
            return None
        
        selected_ticker = st.sidebar.selectbox(
            "Select Ticker",
            available_tickers,
            help="Choose a stock ticker to display"
        )
    else:
        st.sidebar.error("Data manager not initialized")
        return None
    
    # Chart settings section
    st.sidebar.subheader("Chart Settings")
    
    timeframe = st.sidebar.radio(
        "Time Frame",
        options=["Daily", "Weekly", "Monthly"],
        help="Select the candlestick aggregation period"
    )
    timeframe_map = {
        "Daily": "daily",
        "Weekly": "weekly",
        "Monthly": "monthly"
    }
    
    # Chart style selector
    chart_style = st.sidebar.selectbox(
        "Chart Style",
        options=["Candlestick", "Heikin-Ashi", "OHLC Bars"],
        help="Select the chart visualization style"
    )
    chart_style_map = {
        "Candlestick": "candlestick",
        "Heikin-Ashi": "heikin_ashi",
        "OHLC Bars": "bars"
    }
    
    show_volume = st.sidebar.checkbox(
        "Show Volume",
        value=True,
        help="Display volume bars below the chart"
    )
    
    # Theme settings
    st.sidebar.subheader("Theme")
    
    theme = st.sidebar.radio(
        "Chart Theme",
        options=["Light", "Dark"],
        help="Choose light or dark theme"
    )
    theme_lower = theme.lower()
    
    # Chart dimensions
    st.sidebar.subheader("Chart Dimensions")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        width = st.number_input(
            "Width (px)",
            min_value=400,
            max_value=2000,
            value=1200,
            step=100,
            help="Chart width in pixels"
        )
    with col2:
        height = st.number_input(
            "Height (px)",
            min_value=300,
            max_value=1000,
            value=600,
            step=100,
            help="Chart height in pixels"
        )
    
    # Technical Indicators section
    st.sidebar.subheader("📈 Technical Indicators")
    
    available_indicators = []
    if st.session_state.plugin_manager:
        available_indicators = st.session_state.plugin_manager.get_available_plugins()
    
    if available_indicators:
        selected_indicators = st.sidebar.multiselect(
            "Select Indicators",
            available_indicators,
            help="Choose indicators to overlay on the chart"
        )
    else:
        st.sidebar.info("No indicators available")
        selected_indicators = []
    
    # Indicator parameters
    indicator_params = {}
    if selected_indicators:
        with st.sidebar.expander("⚙️ Indicator Parameters", expanded=False):
            for indicator_name in selected_indicators:
                if st.session_state.plugin_manager:
                    indicator = st.session_state.plugin_manager.get_plugin(indicator_name)
                    
                    if indicator:
                        params = indicator.get_parameters()
                        
                        if params:
                            st.write(f"**{indicator_name}**")
                            
                            for param_name, default_value in params.items():
                                param_def = indicator.parameters[param_name]
                                
                                if param_def.type == "int":
                                    value = st.slider(
                                        label=f"{param_name}",
                                        min_value=int(param_def.min_value or 1),
                                        max_value=int(param_def.max_value or 100),
                                        value=int(default_value),
                                        step=int(param_def.step or 1),
                                        key=f"{indicator_name}_{param_name}"
                                    )
                                
                                elif param_def.type == "float":
                                    value = st.slider(
                                        label=f"{param_name}",
                                        min_value=float(param_def.min_value or 0.0),
                                        max_value=float(param_def.max_value or 100.0),
                                        value=float(default_value),
                                        step=float(param_def.step or 0.1),
                                        key=f"{indicator_name}_{param_name}"
                                    )
                                
                                elif param_def.type == "bool":
                                    value = st.checkbox(
                                        label=param_name,
                                        value=default_value,
                                        key=f"{indicator_name}_{param_name}"
                                    )
                                
                                elif param_def.type == "choice":
                                    value = st.selectbox(
                                        label=param_name,
                                        options=param_def.choices,
                                        index=param_def.choices.index(default_value) if default_value in param_def.choices else 0,
                                        key=f"{indicator_name}_{param_name}"
                                    )
                                else:
                                    continue
                                
                                if indicator_name not in indicator_params:
                                    indicator_params[indicator_name] = {}
                                indicator_params[indicator_name][param_name] = value
    
    return {
        'ticker': selected_ticker,
        'timeframe': timeframe_map[timeframe],
        'chart_style': chart_style_map[chart_style],
        'show_volume': show_volume,
        'theme': theme_lower,
        'width': width,
        'height': height,
        'indicators': selected_indicators,
        'indicator_params': indicator_params
    }


def render_main_content(settings):
    """Render the main content area."""
    if not settings:
        return
    
    ticker = settings['ticker']
    timeframe = settings['timeframe']
    theme = settings['theme']
    width = settings['width']
    height = settings['height']
    indicators = settings['indicators']
    indicator_params = settings['indicator_params']
    
    # Update chart engine theme and dimensions
    if st.session_state.chart_engine:
        st.session_state.chart_engine.change_theme(theme)
        st.session_state.chart_engine.width = width
        st.session_state.chart_engine.height = height
    
    # Main title
    st.title(f"📈 {ticker} Stock Chart")
    
    # Display ticker information
    col1, col2, col3, col4 = st.columns(4)
    
    if st.session_state.data_manager:
        try:
            info = st.session_state.data_manager.get_ticker_info(ticker)
            
            with col1:
                st.metric("Current Price", f"${info['current_price']:.2f}")
            
            with col2:
                st.metric("Highest", f"${info['highest_price']:.2f}")
            
            with col3:
                st.metric("Lowest", f"${info['lowest_price']:.2f}")
            
            with col4:
                st.metric("Avg Volume", f"{info['average_volume']:,.0f}")
        
        except Exception as e:
            logger.error(f"Error fetching ticker info: {e}")
    
    # Generate and display chart
    st.subheader("Interactive Chart")
    
    try:
        if st.session_state.chart_engine:
            fig = st.session_state.chart_engine.create_candlestick_chart(
                ticker=ticker,
                timeframe=timeframe,
                chart_style=settings['chart_style'],
                indicators=indicators if indicators else None,
                indicator_params=indicator_params if indicator_params else None,
                show_volume=settings['show_volume']
            )
            
            st.plotly_chart(fig, use_container_width="always")
    
    except Exception as e:
        st.error(f"Error generating chart: {e}")
        logger.error(f"Chart generation error: {e}")
    
    # Display data table
    st.subheader("Data Table")
    
    try:
        if st.session_state.data_manager:
            df = st.session_state.data_manager.get_ohlcv_data(ticker)
            df = st.session_state.data_manager.aggregate_ohlcv(df, timeframe)
            
            # Display table
            st.dataframe(
                df.tail(50).sort_index(ascending=False),
                use_container_width="always",
                height=400
            )
            
            # Export options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv = df.to_csv(index=True)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{ticker}_{timeframe}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    help="Download data as CSV file"
                )
            
            with col2:
                json = df.to_json(orient='index', indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json,
                    file_name=f"{ticker}_{timeframe}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    help="Download data as JSON file"
                )
            
            with col3:
                st.write("💡 **Tip:** Use the range selector buttons on the chart to zoom to specific time periods")
    
    except Exception as e:
        st.error(f"Error displaying data: {e}")
        logger.error(f"Data display error: {e}")
    
    # Indicators information
    if indicators:
        st.subheader("📊 Indicator Information")
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.write("**Active Indicators:**")
            for indicator_name in indicators:
                st.write(f"• {indicator_name}")
        
        with col2:
            with st.expander("📖 Indicator Details", expanded=False):
                if st.session_state.plugin_manager:
                    for indicator_name in indicators:
                        metadata = st.session_state.plugin_manager.get_plugin_metadata(indicator_name)
                        
                        if metadata:
                            st.write(f"**{metadata['name']}** v{metadata['version']}")
                            st.write(f"*{metadata['description']}*")
                            st.write(f"**Author:** {metadata['author']}")
                            
                            if metadata['parameters']:
                                st.write("**Parameters:**")
                                for param_name, param_info in metadata['parameters'].items():
                                    st.write(f"- `{param_name}`: {param_info['description']}")
                            
                            st.divider()


def render_footer():
    """Render the footer."""
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Interactive Market Data Charting v2.0.0**")
    
    with col2:
        st.write("Built with [Streamlit](https://streamlit.io) & [Plotly](https://plotly.com)")
    
    with col3:
        if st.session_state.plugin_manager:
            plugin_count = st.session_state.plugin_manager.get_plugin_count()
            st.write(f"📦 {plugin_count} Indicator Plugins Loaded")


def main():
    """Main application entry point."""
    # Initialize application
    st.session_state.data_manager, st.session_state.chart_engine, st.session_state.plugin_manager = \
        initialize_application()
    
    if not st.session_state.data_manager:
        st.error("Failed to initialize application. Please check your configuration.")
        return
    
    # Render sidebar and get settings
    settings = render_sidebar()
    
    # Render main content
    if settings:
        render_main_content(settings)
    
    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
