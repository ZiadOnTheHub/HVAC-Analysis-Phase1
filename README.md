<div align="center">
  
# 🏢 Commercial HVAC Thermodynamic Analytics Engine (Phase 1)

**A Data Engineering Proof of Concept (POC) evaluating the operational health and thermodynamic efficiency of commercial HVAC systems.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B.svg)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## 📖 Project Overview

Facility managers and energy engineers often struggle to translate raw mechanical data into actionable financial metrics. This pipeline solves that by establishing a thermodynamic baseline for chiller units and cross-referencing their energy load against atmospheric stress (temperature and humidity).

**The interactive dashboard reveals:**
* 🛫 **Operational Cruising Altitude:** Average vs. peak load analysis.
* 🌡️ **Thermodynamic Health (R²):** How well the system responds to actual weather conditions.
* 💰 **Financial Impact:** The exact cost of wasted energy, adjusted for modern commercial electricity rates.

---

## 🏗️ Architecture (The Medallion Pipeline)

The core ETL logic is housed in `hvac_engine.py`, executing a sequential Bronze-Silver-Gold workflow:

### 🥉 Bronze Layer (Raw & Immutable)
* Extracts building meter readings (`max_demo_train.parquet`) and site metadata (`building_metadata.csv`) using Kaggle.
* Dynamically fetches historical hourly weather data via the **Open-Meteo API** based on site coordinates.
* Loads all raw data directly into a local SQLite database using **SQLAlchemy**.

### 🥈 Silver Layer (Cleaned & Joined)
* Executes a **SQL Pushdown** to perform an `INNER JOIN` between the weather and building sensor tables directly in the database.
* Passes data through a **Quality Gate**: filters out negative energy readings and missing weather API data.

### 🥇 Gold Layer (Aggregated Business Logic)
* **Metric 1:** Calculates average and peak chiller loads per quarter.
* **Metric 2:** Uses Multiple Linear Regression (`statsmodels`) to calculate an R-squared score, proving how much variance in energy load is dictated by outside temperature and humidity.
* **Metric 3:** Establishes a "Perfect Day" baseline, isolates hostile weather hours, and calculates the true Financial Penalty in wasted kWh and 2026 dollar equivalents.

---

## 💻 Tech Stack

| Category | Technologies Used |
| :--- | :--- |
| **Core Engine** | Python, Pandas |
| **Database & ORM** | SQLite, SQLAlchemy |
| **Data Science & Modeling** | Statsmodels (Multiple Linear Regression) |
| **Visualization & UI** | Streamlit, Plotly Express / Graph Objects, Pydeck |
| **Data I/O & Export** | Parquet (PyArrow), CSV, Excel (XlsxWriter) |

---

## 🚀 Getting Started

### Prerequisites
Ensure you have **Python 3.9+** installed. You will also need the raw dataset files (`max_demo_train.parquet` and `building_metadata.csv`) placed in the root directory.

### Installation
Clone the repository and move into the project directory:
```bash
git clone [https://github.com/ZiadOnTheHub/HVAC-Analysis-Phase1.git](https://github.com/ZiadOnTheHub/HVAC-Analysis-Phase1.git)
cd HVAC-Analysis-Phase1

### Execution Methods

**Option A: Run the Interactive Dashboard (Recommended) Launch the Streamlit UI to explore the data visually, view building maps, and download Gold-layer CSV artifacts.
streamlit run app.py

**Option B: Run the CLI Engine Run the backend ETL pipeline directly from your terminal to get quick financial penalty summaries.
python main.py

### 📂 Project Structure

📦 HVAC-Analysis-Phase1/
├── 📄 app.py                  # Streamlit frontend dashboard
├── ⚙️ hvac_engine.py          # Core ETL Medallion pipeline logic
├── 🖥️ main.py                 # Command-line interface runner
├── 🔧 config.py               # Static configuration (coordinates, DB URI)
├── 📚 requirements.txt        # Python package dependencies
├── 📊 max_demo_train.parquet  # Raw building sensor data
└── 🗺️ building_metadata.csv   # Raw building locations
