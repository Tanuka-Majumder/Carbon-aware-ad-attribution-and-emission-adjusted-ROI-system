# AdEco - Carbon-Aware Ad Attribution & Emission-Adjusted ROI 🌿

A sustainability-driven analytics platform that integrates **carbon emissions** into **multi-touch ad attribution**. Designed for performance marketing, ESG, and analytics teams to align **advertising efficiency** with **environmental impact**.


## 📊 Project Overview

Traditional attribution models optimize for cost and conversions, ignoring environmental impact. **AdEco** introduces a **Green Attribution Framework** that augments digital ad journeys with emissions data, enabling **climate-conscious optimization** across marketing channels.

This end-to-end pipeline performs:

- Carbon emissions estimation per ad impression
- Attribution scoring 
- ESG-aware KPI generation
- Streamlit-powered dashboard for real-time insights


## ✅ Core Functionalities

### 1. 🔁 Multi-Touch Attribution
- Processes ad journeys like: `Email → Google Ad → YouTube → Conversion`
- ML-based attribution using logistic regression or Shapley values

### 2. 🧮 Carbon Emissions Estimation
- Maps each ad impression to average CO₂ (in grams) using a sustainability lookup table
- Supports formats like:
  - Email: low (0.3 gCO₂)
  - Display Ads: moderate (1.2 gCO₂)
  - YouTube 1080p: high (3.5 gCO₂)
  - TikTok/Influencer: variable

### 3. 🌱 Green Attribution Score
- Introduces a **sustainability-adjusted performance metric**:

   **Green Score** = Attribution Score / Emissions (gCO₂)

Ranks channels based on high performance and low carbon footprint.

### 4. 📈 ESG-Aware KPIs 
- **CCPA** – Carbon Cost per Acquisition
- **eROAS** – Emissions-Adjusted Return on Ad Spend
- **Sustainability Efficiency** = Conversions / kg CO₂

## 🚀 Dashboard Preview

Built with [Streamlit](https://streamlit.io/) for real-time ESG visibility:

- Total and average emissions per journey
- Emissions breakdown per ad channel
- Downloadable journey-level and channel-level CSVs
- Attribution vs Green Score visualizations
- KPI cards and sustainability alerts

## 🚧 Future Work

- Real-time CO₂ per impression via APIs
- ESG report auto-export (PDF, XLS)
- Integration with ad platforms 
