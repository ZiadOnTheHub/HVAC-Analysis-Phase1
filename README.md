🏢 Commercial HVAC Thermodynamic Analytics Engine (Phase 1)
A Phase 1 Data Engineering Proof of Concept (POC) evaluating the operational health and thermodynamic efficiency of commercial HVAC systems.

This project uses a Medallion Architecture to extract building sensor data and historical weather metrics, transform them via SQL pushdowns, and calculate the direct financial penalty of mechanical inefficiencies.

📖 Project Overview
Facility managers and energy engineers often struggle to translate raw mechanical data into actionable financial metrics. This pipeline solves that by establishing a thermodynamic baseline for chiller units and cross-referencing their energy load against atmospheric stress (temperature and humidity).

The end result is an interactive dashboard that reveals:

Operational Cruising Altitude: Average vs. peak load analysis.

Thermodynamic Health (R²): How well the system responds to actual weather conditions.

Financial Impact: The exact cost of wasted energy, adjusted for modern commercial electricity rates.

🏗️ Architecture (The Medallion Pipeline)
The core ETL logic is housed in hvac_engine.py, executing a sequential Bronze-Silver-Gold workflow:

🥉 Bronze Layer (Raw & Immutable):

Extracts building meter readings (max_demo_train.parquet) and site metadata (building_metadata.csv) using kaggle.

Dynamically fetches historical hourly weather data via the Open-Meteo API based on site coordinates.

Loads all raw data directly into a local SQLite database using SQLAlchemy.

🥈 Silver Layer (Cleaned & Joined):

Executes a SQL Pushdown to perform an INNER JOIN between the weather and building sensor tables directly in the database.

Passes data through a Quality Gate: filters out negative energy readings and missing weather API data.

🥇 Gold Layer (Aggregated Business Logic):

Metric 1: Calculates average and peak chiller loads per quarter.

Metric 2: Uses Multiple Linear Regression (statsmodels) to calculate an R-squared score, proving how much variance in energy load is dictated by outside temperature and humidity.

Metric 3: Establishes a "Perfect Day" baseline, isolates hostile weather hours, and calculates the true Financial Penalty in wasted kWh and 2026 dollar equivalents.

💻 Tech Stack

Core Engine: Python, Pandas 


Database & ORM: SQLite, SQLAlchemy 


Data Science & Modeling: Statsmodels (Multiple Linear Regression) 


Visualization & UI: Streamlit , Plotly Express / Graph Objects , Pydeck 

File Formats: Parquet (pyarrow), CSV


🚀 Getting Started

Prerequisites

Ensure you have Python 3.9+ installed. You will also need the raw dataset files (max_demo_train.parquet and building_metadata.csv) placed in the root directory.

Installation
Clone the repository:
git clone https://github.com/ZiadOnTheHub/HVAC-Analysis-Phase1.git
cd HVAC-Analysis-Phase1


Install the required dependencies:
pip install -r requirements.txt
Execution Methods

Option A: Run the Interactive Dashboard (Recommended)
Launch the Streamlit UI  to explore the data visually, view building maps, and download Gold-layer CSV artifacts.
streamlit run app.py

Option B: Run the CLI Engine
Run the backend ETL pipeline directly from your terminal to get quick financial penalty summaries.

python main.py
📂 Project Structure
├── app.py                  # Streamlit frontend dashboard
├── hvac_engine.py          # Core ETL Medallion pipeline logic
├── main.py                 # Command-line interface runner
├── config.py               # Static configuration (coordinates, DB URI)
├── requirements.txt        # Python package dependencies
├── max_demo_train.parquet  # Raw building sensor data (Using Kaggle API)
└── building_metadata.csv   # Raw building locations (Using Kaggle API)

🔮 Phase 2 Roadmap
the next iteration of this project will focus on scalability:

Persistent Storage: Transitioning from an overwriting SQLite database to a persistent Data Warehouse (e.g., PostgreSQL or Snowflake) or a Data Lake (partitioned Parquet files).

Orchestration: Wrapping the ETL engine in a modern orchestrator like Mage.ai, Dagster, or Prefect for scheduled runs and automated retries.
