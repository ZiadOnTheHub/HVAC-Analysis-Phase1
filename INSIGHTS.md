# 📊 Deep Dive: HVAC Thermodynamic Analytics & Root Cause Analysis

This document provides the technical findings surfaced by the **HVAC Analytics Engine (Phase 1)**. While the pipeline is designed to audit building profiles at scale, this analysis focuses on **Building 7** as a primary case study for critical mechanical failure.

---

## 1. Statistical Framework & Model Performance

To move beyond basic energy averaging, the engine implements a **Multiple Linear Regression (OLS)** model to predict the expected electrical load ($\hat{L}$) based on environmental stressors.

### The Predictive Model
The relationship between atmospheric stress and power consumption is modeled using Ordinary Least Squares:

$$
\hat{L} = \beta_0 + \beta_T T + \beta_H H + \epsilon
$$

**Where:**
* **$T$**: Outdoor Dry-Bulb Temperature (°C).
* **$H$**: Relative Humidity ($RH$ %).
* **$\beta_0$**: The intercept, representing the building's "Baseload" (internal heat from servers, lighting, and occupants).
* **$\epsilon$**: Residual error (The "Inefficiency Gap").

---

## 2. Operational Findings: Root Cause Hypotheses

By analyzing the "Gold Layer" metrics specifically the **Operational Baseline** and **Thermodynamic Stress Test** we can categorize mechanical failures remotely.

### 🚩 Persistent Positive Residuals (Inefficiency)
* **Observation:** Actual load consistently exceeds the "Perfect Day" baseline (18°C–22°C, <50% humidity).
* **Hypothesis:** Fouled condenser coils or simultaneous heating/cooling conflicts. The system is working harder than required to achieve the same cooling effect.

### 🚩 Seasonal Sensitivity
* **Observation:** Performance varies significantly by month. Missing $R^2$ bars in the dashboard indicate periods where sensor readings were insufficient or non-responsive.
* **Hypothesis:** Stuck outdoor air dampers. If performance drops during "shoulder seasons," the system is likely failing to utilize free outdoor air for cooling.

---

## 3. Visual Diagnostics: Interpreting Atmospheric Stress Plots

The scatter plots in the dashboard map **Color → Humidity** ($RH$). Interpreting the relationship between point brightness and vertical position (Load) reveals deep mechanical insights.

### Practical Rules for Dark vs. Light Points
* **Dark Points (High $RH$):** Usually represent higher load because latent cooling (dehumidification) adds significant energy demand.
* **Light Points (Low $RH$):** Usually represent lower load as the system handles only "Sensible" heat.

### 🚩 Why a Dark Point can show Low Energy (Anomalous)
1. **Economizer/Free-Cooling:** High outdoor humidity but low dry-bulb temperature may allow the system to reduce compressor runtime if controls use enthalpy-based logic.
2. **Internal Load Variability:** Low occupancy or equipment downtime during a humid day.
3. **Sensor Drift:** The $RH$ sensor may be "stuck high" while actual conditions are dry.

### 🚩 Why a Light Point can show High Energy (Anomalous)
1. **High Internal Sensible Loads:** Heavy server room activity or solar gains raising the load despite low outdoor humidity.
2. **Hardware Faults:** Fouled coils or low refrigerant charge forcing higher power draw for the same ambient conditions.
3. **Control Conflict:** Simultaneous heating and cooling occurring due to improper setpoint deadbands.

---

## 4. Diagnostic Checklist & Decision Matrix

To move from observation to action, use the following tiered verification process:

### Tier 1: Digital Validation
* **[ ] Sensor Sanity:** Compare building $RH$ sensors to nearby weather stations; check for sudden "plateaus" in data.
* **[ ] Control Mode Log:** Confirm if economizer or night-cooling schedules were active during flagged timestamps.
* **[ ] Enthalpy Test:** Compute moist-air enthalpy ($h$) and replot load. If anomalies vanish, the issue is standard latent-load physics.

### Tier 2: Physical Field Checks
* **[ ] Residual Analysis:** Look for systematic bias in residuals ($Actual - \hat{L}$) conditioned on hour-of-day to identify scheduling errors.
* **[ ] Component Audit:** Inspect coil $\Delta T$, compressor amperage, and valve positions for persistent positive residuals.

### Quick Decision Table
| Anomaly | Likely Cause | Quick Diagnostic | Corrective Action |
| :--- | :--- | :--- | :--- |
| **Dark + Low Load** | Sensor stuck high; Economizer active | Compare $RH$ to reference station | Calibrate sensor; Review enthalpy logic |
| **Light + High Load** | Internal sensible gains; Hardware fault | Check occupancy & coil $\Delta T$ | Inspect/Clean coils; Tune schedules |
| **Dark + High Load** | Expected (Latent + Sensible) | Replot vs. Enthalpy index | Optimize setpoints; Check latent control |

---

## 5. Financial Impact Decomposition

### Case Study: Building 7 Technical Profile
| Attribute | Value |
| :--- | :--- |
| **Location** | Orlando, Florida (Site 0) |
| **Meter Type** | Chilled Water (Meter 1) |
| **Analysis Year** | 2016 |
| **Total Annual Loss (2026 Eq)** | **$1,627,199** |
| **Energy Rate (2026 Eq)** | **$0.141/kWh** |

**Key Driver:** Shoulder-season inefficiency. The system fails to modulate down during moderate temperatures, effectively "ghost loading" the utility meter.

---

> **Note:** For a live interactive view, visit the [Streamlit Dashboard](https://hvac-analysis-phase1.streamlit.app/).
