import pandas as pd
import requests
from sqlalchemy import create_engine
import config
import statsmodels.api as sm
import pyarrow
class HVACAnalyticsEngine:
    """

    An end-to-end data pipeline for extracting, transforming, and analyzing
    HVAC chiller performance against meteorological data.

    """

    def __init__(self, building_id: int):
        self.building_id = building_id
        self.meter_type = config.METER_TYPE
        self.weather_year = config.WEATHER_YEAR
        self.engine = create_engine(config.DATABASE_URI)
        self.silver_data = None

    def execute_bronze_layer(self):
        """

        This is where the data is extracted, gets loaded as is in the database.
        Kaggle was used to extract train.csv and building_metadata.csv in bronze_extractor.py,
        for the weather data, we use the archive in Open-Meteo API.

        """
        print(f"--- Initiating Bronze Layer for Building {self.building_id} ---")

        ## Loading Local Metadata
        try:
            building_df = pd.read_parquet('max_demo_train.parquet')
            location_df = pd.read_csv("building_metadata.csv")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Missing essential raw data files. {e}")

        # Filtering the building in a separate DataFrame
        target_building = building_df[
            (building_df['building_id'] == self.building_id) &
            (building_df['meter'] == self.meter_type)
            ].copy()

        # Getting the location filter
        target_location = location_df[location_df["building_id"] == self.building_id].copy()

        # Safe exit in case there's no data found
        if target_location.empty:
            raise ValueError(f"Building {self.building_id} not found in metadata or has no Chilled Water data.")

        # Getting the site location ready to use for Weather Data Extraction
        site_id = target_location['site_id'].iloc[0]
        latitude, longitude = config.SITE_COORDINATES.get(site_id, config.SITE_COORDINATES[0])
        print(f"Discovered Building {self.building_id} is at Site {site_id}. Coordinates: ({latitude}, {longitude})")

        ## Extracting Weather Data (Open-Meteo API)
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": f"{self.weather_year}-01-01",
            "end_date": f"{self.weather_year}-12-31",
            "hourly": ["temperature_2m", "relative_humidity_2m"],
            "timezone": "America/New_York"
        }

        print("Fetching weather data...")
        try:
            response = requests.get(url=url, params=params)
            response.raise_for_status()
            data = response.json()

            hourly_weather_data = data['hourly']
            weather_df = pd.DataFrame({
                "timestamp": hourly_weather_data["time"],
                "temp_c": hourly_weather_data["temperature_2m"],
                "humidity": hourly_weather_data["relative_humidity_2m"]
            })
            print("API Extraction Successful.")

        # Safe exit in case the API extraction fails
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"API Extraction Failed: {e}")

        ## Standardize and Load to Database
        weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
        target_building['timestamp'] = pd.to_datetime(target_building['timestamp'])

        target_location.to_sql("bronze_metadata", con=self.engine, if_exists='replace', index=False)
        weather_df.to_sql("bronze_weather", con=self.engine, if_exists='replace', index=False)
        target_building.to_sql("bronze_building_readings", con=self.engine, if_exists='replace', index=False)
        print("Bronze tables successfully loaded to SQLite.\n")

    def execute_silver_layer(self):
        """

        Joining the weather and reading tables in one table
        and passing it by the data quality gate to make sure the data is ready for the final analysis phase.

        """

        print("--- Initiating Silver Layer Transformations (SQL Pushdown) ---")

        ## The Join Query
        join_query = """
            SELECT 
                r.timestamp,
                r.meter_reading,
                w.temp_c,
                w.humidity
            FROM bronze_building_readings r
            INNER JOIN bronze_weather w
                ON r.timestamp = w.timestamp
        """

        # We only pull the finalized, perfectly joined data into Python memory
        merged_table = pd.read_sql(join_query, con=self.engine)

        # Ensure timestamp is a datetime object so we can extract dates
        merged_table['timestamp'] = pd.to_datetime(merged_table['timestamp'])

        ## 🚨 THE DATA QUALITY GATE 🚨
        initial_rows = len(merged_table)

        # Dropping negative energy readings
        merged_table = merged_table[merged_table['meter_reading'] >= 0]

        # Dropping hours where the weather API failed to return data
        merged_table = merged_table.dropna(subset=['temp_c', 'humidity'])

        print(f"Quality Gate cleared. Filtered out {initial_rows - len(merged_table)} corrupted rows.")

        # Adding time dimensions for the Gold layer aggregations
        merged_table['quarter'] = merged_table['timestamp'].dt.quarter
        merged_table['month'] = merged_table['timestamp'].dt.month

        self.silver_data = merged_table
        print("Silver layer transformations complete. SQL Join successful!\n")

    def execute_gold_layer(self):
        """

        This is where the analytics & fact extracting belong.

        """
        print("--- Initiating Gold Layer Analytics ---")
        df = self.silver_data

        # Handling the failure of the silver layer
        if df is None or df.empty:
            raise ValueError("Silver data is missing. Run execute_silver_layer() first.")

        ## Metric 1: The Operational Baseline
        # This metric calculates the peak and average loads for each quarter of the year.
        workdays_df = df[df['timestamp'].dt.dayofweek < 5].copy()
        gold_metric_1 = workdays_df.groupby('quarter').agg(
            avg_quarterly_load_KWh=('meter_reading', 'mean'),
            peak_load_KWh=('meter_reading', 'max')
        ).reset_index()

        peak_indices = workdays_df.groupby('quarter')['meter_reading'].idxmax()
        gold_metric_1['peak_date'] = workdays_df.loc[peak_indices, 'timestamp'].dt.date.values
        gold_metric_1['peak_day_name'] = workdays_df.loc[peak_indices, 'timestamp'].dt.day_name().values
        gold_metric_1['peak_hour'] = workdays_df.loc[peak_indices, 'timestamp'].dt.hour.values

        ## Metric 2: Thermodynamic Stress Test (Upgraded to Multiple Regression)
        # R-squared measures the variance explained by BOTH temperature and humidity.
        print("Running Multiple Linear Regression for Metric 2...")

        def calculate_combined_r2(month_df):
            """

             Metric 2 uses Multiple Linear Regression (R-squared) to measure how much
             both temperature AND humidity dictate the chiller load. The 'constant' accounts
             for the building's baseline internal heat (servers, people). A high R² (>0.6)
             means healthy, weather-driven cooling; a low R² means the system is rogue.

            """
            # Drop empty rows to prevent the math engine from crashing
            clean_df = month_df.dropna(subset=['temp_c', 'humidity', 'meter_reading'])

            # If a month has no data, return NaN
            if len(clean_df) < 10:
                return pd.NA

            # X = The Weather
            X = clean_df[['temp_c', 'humidity']]
            X = sm.add_constant(X)  # Adds the y-intercept baseline

            # y = The Chiller Load
            y = clean_df['meter_reading']

            # Fit the model and return the R-squared value
            model = sm.OLS(y, X).fit()
            return model.rsquared

        ## Apply the regression to every month
        gold_metric_2 = df.groupby('month').apply(calculate_combined_r2).reset_index(name='r_squared_value')

        def assess_combined_health(r2):
            """

            This is where we assess and give the standard for r2 and tell the user about the chiller status.

            """
            if pd.isna(r2):
                return "Insufficient Data"
            elif r2 > 0.60:
                return "Excellent"
            elif r2 > 0.40:
                return "Normal"
            else:
                return "Warning: Check Controls/Overrides"

        gold_metric_2['system_health'] = gold_metric_2['r_squared_value'].apply(assess_combined_health)
        # Notice how we used .apply() only because we're running the loop 12 time only,
        # however it's terrible for the performance.

        ## Metric 3: The Weather-Driven Financial Toll (Total Wasted Energy)
        print("Calculating the Annual Weather Penalty...")

        # Establishing the "Perfect Day" Baseline (Sensible cooling only, no latent heat)
        mild_mask = (df['temp_c'] >= 18) & (df['temp_c'] <= 22) & (df['humidity'] < 50)
        baseline_avg_load = df[mild_mask]['meter_reading'].mean()

        # Fallback safeguard in case a location (like a desert) has zero "mild" days
        if pd.isna(baseline_avg_load) or baseline_avg_load == 0:
            baseline_avg_load = df[df['meter_reading'] > 0]['meter_reading'].quantile(0.10)

        # Isolating the "Weather Penalty" hours
        # filtered for hours, where the weather was actively hostile (Hot OR Humid)
        # AND the chiller was forced to work harder than the perfect day baseline.
        hostile_weather_mask = (df['temp_c'] > 22) | (df['humidity'] >= 50)
        overworked_mask = (df['meter_reading'] > baseline_avg_load)

        penalty_df = df[hostile_weather_mask & overworked_mask]

        # Calculating the Totals
        # Sum the exact delta of energy wasted ABOVE the baseline during those hostile hours
        total_kwh = penalty_df['meter_reading'].sum()
        wasted_kwh = (penalty_df['meter_reading'] - baseline_avg_load).sum()
        total_operating_hours = len(df[df['meter_reading'] > 0])
        expected_annual_kwh = baseline_avg_load * total_operating_hours

        # Translating to Business Value ($$$)
        # The average US commercial electricity rate in 2016 was ~$0.104 per kWh
        kwh_rate = 0.104
        wasted_dollars = wasted_kwh * kwh_rate
        kwh_rate_2026_equivalent = 0.141
        wasted_dollars_2026_equivalent = wasted_kwh * kwh_rate_2026_equivalent
        print(f"Gold layer metrics calculated. Wasted Cost: ${wasted_dollars:,.2f}\nWasted Cost 2026 Equivalent: ${wasted_dollars_2026_equivalent:,.2f}\n")

        # returning analysis values
        return {
            "silver_table": df,
            "metric_1": gold_metric_1,
            "metric_2": gold_metric_2,
            "expected_kwh": baseline_avg_load,
            "expected_annual_kwh": expected_annual_kwh,
            "total_kwh": total_kwh,
            "wasted_kwh": wasted_kwh,
            "wasted_dollars": wasted_dollars,
            "wasted_dollars_2026_equivalent": wasted_dollars_2026_equivalent
        }

    def run_full_pipeline(self):
        self.execute_bronze_layer()
        self.execute_silver_layer()
        return self.execute_gold_layer()