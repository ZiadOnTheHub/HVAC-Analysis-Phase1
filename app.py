import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from hvac_engine import HVACAnalyticsEngine
import config
import pydeck as pdk
import io

# ==========================================
# CONFIG & CSS
# ==========================================
st.set_page_config(
    page_title="HVAC Analytics",
    page_icon="🏢",
    layout="wide"
)

def get_building_location(building_id):
    # Load metadata to find the site_id for this building
    meta = pd.read_csv("building_metadata.csv")
    site_id = meta.loc[meta['building_id'] == building_id, 'site_id'].values[0]

    # Get lat/lon from your SITE_COORDINATES dict
    coords = config.SITE_COORDINATES.get(site_id, (0, 0))
    return pd.DataFrame({'lat': [coords[0]], 'lon': [coords[1]]})

st.markdown("""
    <style>
    .intro-box { background-color: #f8fafc; padding: 25px; border-radius: 8px; border-left: 5px solid #1e3a8a; margin-bottom: 30px; color: #334155; }
    .loss-warning { background-color: #fef2f2; color: #b91c1c; padding: 15px; border-radius: 5px; border-left: 5px solid #ef4444; font-weight: bold; margin-top: 10px; }
    .loss-acceptable { background-color: #fffbeb; color: #b45309; padding: 15px; border-radius: 5px; border-left: 5px solid #f59e0b; font-weight: bold; margin-top: 10px; }
    .loss-success { background-color: #f0fdf4; color: #15803d; padding: 15px; border-radius: 5px; border-left: 5px solid #22c55e; font-weight: bold; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# CACHING & HELPERS
# ==========================================
# Added ttl (time-to-live of 1 hour) and max_entries to prevent memory bloat
@st.cache_data(show_spinner=False, ttl=3600, max_entries=5)
def load_pipeline_results(building_id: int):
    engine = HVACAnalyticsEngine(building_id=building_id)
    return engine.run_full_pipeline()



@st.cache_data
def convert_df_to_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return buffer.getvalue()


def generate_insights(results):
    avg_r2 = results['metric_2']['r_squared_value'].mean()
    wasted = results['wasted_dollars_2026_equivalent']
    if avg_r2 < 0.5:
        issue = "Poor weather responsiveness — indicative of control overrides or faulty mechanical sensors."
    else:
        issue = "System responds optimally to environmental conditions."
    return {"avg_r2": avg_r2, "issue": issue, "waste": wasted}


# ==========================================
# SESSION STATE INITIALIZATION (FIX 2 & 3)
# ==========================================
# This acts as the app's memory so it doesn't forget the pipeline ran
if 'pipeline_run' not in st.session_state:
    st.session_state.pipeline_run = False
if 'current_building' not in st.session_state:
    st.session_state.current_building = 7

# ==========================================
# UI & SIDEBAR
# ==========================================
st.title("🏢 HVAC Thermodynamic Analytics Engine")

st.markdown("""
<div class="intro-box">
    <h3 style="margin-top:0px; color:#0f172a;">📖 Project Overview: Thermodynamic Efficiency & Financial Impact</h3>
    <p>This data engineering pipeline evaluates the operational health of commercial HVAC systems by combining building meter readings with historical meteorological data (via the Open-Meteo API). The goal is to translate thermodynamic inefficiency directly into financial ROI.</p>
    <p><b>1. Operational Baseline:</b> We establish the building's normal "cruising altitude" by calculating average vs. peak chiller loads. A massive gap indicates extreme environmental vulnerability.</p>
    <p><b>2. Thermodynamic Performance (R²):</b> A healthy system scales its energy use seamlessly with Outside Temp + Humidity. A high R² score means the weather is correctly driving the system. A low score means the system is wasting energy due to stuck valves or manual overrides.</p>
    <p><b>3. Financial Impact:</b> We isolate hostile weather hours, calculate the exact energy wasted above a "Perfect Weather" baseline, and multiply it by modern commercial energy rates ($0.141/kWh) to reveal the true cost of inefficiency.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Pipeline Controls")

    # Dynamically extract the valid IDs straight from the Parquet file!
    # By specifying columns=['building_id'], it loads lightning fast.
    valid_ids = pd.read_parquet('max_demo_train.parquet', columns=['building_id'])['building_id'].unique().tolist()
    
    building_id = st.selectbox(
        "Select a Valid Building ID",
        options=valid_ids,
        index=valid_ids.index(7)
    )

    # If the user changes the ID, reset the app memory so it prompts them to run it again
    if building_id != st.session_state.current_building:
        st.session_state.pipeline_run = False
        st.session_state.current_building = building_id

    st.markdown("---")
    st.subheader("Chart Filters")
    selected_quarter = st.selectbox(
        "Select Quarter for Scatter Plot",
        options=["All Year", "Q1 (Jan-Mar)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Oct-Dec)"]
    )

    st.markdown("---")
    # When clicked, we lock the session state to True
    if st.button("🚀 Run ETL Pipeline", use_container_width=True):
        st.session_state.pipeline_run = True

# If the pipeline hasn't run yet, stop the script here.
if not st.session_state.pipeline_run:
    st.info("👈 Select a building ID in the sidebar and click 'Run ETL Pipeline' to initialize.")
    st.stop()

# ==========================================
# LOAD DATA & EXECUTE PIPELINE
# ==========================================
with st.spinner("Executing Medallion Pipeline (Extracting, Transforming, Aggregating)..."):
    try:
        results = load_pipeline_results(building_id)
        insights = generate_insights(results)

        # --- EXECUTIVE SUMMARY & LOCATION ---
        st.header("📌 Executive Summary")

        # Create two columns: one for metrics, one for the map
        summary_col, map_col = st.columns([2, 1])

        with summary_col:
            m1, m2 = st.columns(2)
            m1.metric("Avg System R²", f"{insights['avg_r2']:.2f}")
            m2.metric("Total Financial Loss", f"${insights['waste']:,.0f}")
            st.write(f"**System Status Analysis:**")
            st.info(insights['issue'])

        with map_col:
            loc_data = get_building_location(building_id)
            # A clean, zoomed-in map of the building site
            st.map(loc_data, zoom=10, use_container_width=True)
            st.caption(f"📍 Analysis Site (Lat: {loc_data['lat'][0]}, Lon: {loc_data['lon'][0]})")

        # --- METRIC 1: OPERATIONAL BASELINE ---
        st.subheader("Operational Baseline (Gold Layer)")
        df = results['metric_1']
        fig = go.Figure([
            go.Bar(x=df['quarter'], y=df['avg_quarterly_load_KWh'], name='Avg Load', marker_color='#93c5fd'),
            go.Bar(x=df['quarter'], y=df['peak_load_KWh'], name='Peak Load', marker_color='#1d4ed8')
        ])
        fig.update_layout(barmode='group',
                          xaxis=dict(title="Quarter", tickvals=[1, 2, 3, 4], ticktext=['Q1', 'Q2', 'Q3', 'Q4']),
                          yaxis_title="Chiller Load (kWh)")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")

        # --- METRIC 2: THERMODYNAMIC PERFORMANCE ---
        st.subheader("Thermodynamic Performance (R²)")
        df2 = results['metric_2']
        fig2 = px.bar(df2, x="month", y="r_squared_value", color_discrete_sequence=['#2563eb'])
        fig2.update_layout(xaxis=dict(tickmode='linear', dtick=1), yaxis_title="R² Score")
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("ℹ️ *Missing bars indicate insufficient sensor readings for that period.*")
        st.markdown("---")

        # --- SCATTER PLOT (Interactive) ---
        st.subheader("Load vs. Atmospheric Stress")
        silver_df = results['silver_table']

        # Apply the filter based on the Selectbox memory!
        if selected_quarter != "All Year":
            q_map = {"Q1 (Jan-Mar)": 1, "Q2 (Apr-Jun)": 2, "Q3 (Jul-Sep)": 3, "Q4 (Oct-Dec)": 4}
            silver_df = silver_df[silver_df['quarter'] == q_map[selected_quarter]]

        sample = silver_df.sample(n=min(2000, len(silver_df)), random_state=42)
        fig3 = px.scatter(
            sample, x="temp_c", y="meter_reading", color="humidity", trendline="lowess",
            color_continuous_scale=px.colors.sequential.Blues,
            labels={"temp_c": "Outside Temp (°C)", "meter_reading": "Chiller Load (kWh)", "humidity": "Humidity %"}
        )
        fig3.update_traces(
            hovertemplate="<b>Temp:</b> %{x:.1f}°C<br><b>Load:</b> %{y:.0f} kWh<br><b>Humidity:</b> %{marker.color:.0f}%")
        fig3.update_layout(title=f"Atmospheric Stress ({selected_quarter})")
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("---")

        # --- FINANCIAL KPI & WASTE ---
        st.subheader("Financial Impact")
        k1, k2, k3 = st.columns(3)
        k1.metric("Expected Baseline", f"{results['expected_annual_kwh']:,.0f} kWh")
        k2.metric("Inefficient Load", f"{results['wasted_kwh']:,.0f} kWh")
        k3.metric("Loss (At $0.141/kWh)", f"${results['wasted_dollars_2026_equivalent']:,.0f}")

        expected_kwh = results['expected_annual_kwh']
        wasted_kwh = results['wasted_kwh']
        waste_pct = (wasted_kwh / expected_kwh) * 100 if expected_kwh > 0 else 100.0

        if waste_pct < 15:
            st.markdown(f'<div class="loss-success">✅ EXCELLENT EFFICIENCY ({waste_pct:.1f}% Waste)</div>',
                        unsafe_allow_html=True)
        elif waste_pct < 25:
            st.markdown(f'<div class="loss-acceptable">⚠️ ACCEPTABLE EFFICIENCY ({waste_pct:.1f}% Waste)</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="loss-warning">🚨 CRITICAL DEVIATION ({waste_pct:.1f}% Waste) - ${results["wasted_dollars_2026_equivalent"]:,.0f} penalty.</div>',
                unsafe_allow_html=True)
        st.markdown("---")

        # --- DATA EXPORT ---
        st.subheader("💾 Export Gold Layer Artifacts")
        dl_col1, dl_col2 = st.columns(2)


        dl_col1.download_button(
            label="Download Operational Baseline (Excel)",
            data=convert_df_to_excel(results['metric_1']),
            file_name=f"bld_{building_id}_operational_baseline.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        dl_col2.download_button(
            label="Download R² Performance Data (Excel)",
            data=convert_df_to_excel(results['metric_2']),
            file_name=f"bld_{building_id}_thermodynamic_r2.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Engine Failure: {e}")
        st.warning(
            "⚠️ Try entering a different Building ID (e.g., 166, 1409, or 1410) that contains valid Chilled Water (Meter 1) data.")
