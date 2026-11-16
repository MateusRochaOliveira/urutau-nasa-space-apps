<p align="center">
  <img src="assets/logo_urutau.svg" alt="URUTAU Logo" width="420">
</p>

<h3 align="center">Agrometeorological Intelligence & Lunar Planting Calendar for Semi-Arid Smallholder Farmers</h3>

<p align="center">
  <strong>NASA Space Apps Challenge</strong> • Target Region: <strong>Araçuaí, MG — Jequitinhonha Valley, Brazil</strong> (<code>-16.8541° S, -42.0606° W</code>)
</p>

---

### 🔗 Live Demo & Source Code
* **Interactive Web App:** [https://urutau-nasa-space-apps.streamlit.app](https://urutau-nasa-space-apps.streamlit.app) *(update with your exact Streamlit Cloud URL)*
* **Repository:** [github.com/MateusRochaOliveira/urutau-nasa-space-apps](https://github.com/MateusRochaOliveira/urutau-nasa-space-apps)

---

### 🌍 Overview & Problem Statement
Smallholder farmers in the semi-arid **Jequitinhonha Valley** face severe rainfall irregularity and thermal stress. Traditional planting decisions often rely solely on empirical lunar calendars, which—when disconnected from real orbital soil-moisture and temperature data—can lead to seed loss during false starts of the rainy season.

**URUTAU** bridges **NASA Earth observation data**, **FAO crop physiology thresholds**, and **astronomical lunar ephemerides** into a fast, offline-resilient decision-support dashboard that answers two core questions for any planting date (`2026–2035` perennial horizon):
1. **What should I plant now?** (Automated multi-crop suitability ranking based on 7-day rainfall, thermal comfort, and lunar phase alignment).
2. **When is the safest sowing window?** (Real-time moisture recharge tracking combined with seasonal Day-of-Year projections for future planning).

---

## Data Engineering & Provenance (`data/`)

To guarantee scientific reproducibility, low latency, and reliable execution in rural areas of the **Jequitinhonha Valley (Minas Gerais, Brazil)** with limited internet connectivity, URUTAU operates on three curated datasets stored locally in the `data/` directory.

### 1. Agrometeorological & Climate Data — NASA POWER
- **File:** `data/nasa_power_jequitinhonha.csv` *(renamed from `POWER_Point_Daily_20260101_20261115_016d85S_042d06W_LST.csv`)*
- **Official Source:** [NASA POWER Data Access Viewer](https://power.larc.nasa.gov/data-access-viewer/) (*Prediction Of Worldwide Energy Resources — MERRA-2 Source*).
- **Spatial & Temporal Scope:** Single-point extraction configured for the **Agroclimatology** user community at **Daily** temporal resolution (`2026-01-01` through `2026-11-15`, totaling 319 daily records). The dataset uses a single representative reference coordinate centered on **Araçuaí, MG** (`Latitude: -16.8541`, `Longitude: -42.0606`, average grid elevation: `684.58 m`), serving as the climatic benchmark for the Middle Jequitinhonha Cerrado–Caatinga transition zone. For multi-year planning beyond the observed window (`2027–2035`), the engine projects seasonal climatological baselines via Day-of-Year (`DOY`) analogs.
- **Extracted Variables & Preprocessing:**
  * `T2M`: MERRA-2 Air Temperature at 2 Meters ($^\circ\text{C}$), with automated diurnal amplitude estimation (`T2M_MAX`, `T2M_MIN`) when sub-daily extremes are omitted.
  * `RH2M`: MERRA-2 Relative Humidity at 2 Meters ($\%$).
  * `PRECTOTCORR`: MERRA-2 Bias-Corrected Precipitation ($\text{mm/day}$), aggregated into a 7-day rolling moisture recharge metric (`RAIN_7D`).
  * *Data Cleaning:* Sentinel missing values (`-999.0`, resulting from standard 2–3 day satellite assimilation latency at the end of the extraction window) are masked during ingestion prior to statistical aggregation.

### 2. Crop Ecological & Physiological Requirements — FAO EcoCrop
- **File:** `data/ecocrop.parquet`
- **Official Source:** [FAO EcoCrop Database](https://data.apps.fao.org/catalog/dataset/ecocrop) via the *CGIAR Climate Action Data Hub* (Version 1, Apache Parquet columnar format, 55 physiological and edaphoclimatic variables).
- **Curation Methodology:** Filtered for traditional and drought-adapted crops relevant to family farming in the Jequitinhonha Valley (*Zea mays*, *Phaseolus vulgaris*, *Manihot esculenta*, *Sorghum bicolor*, *Vigna unguiculata*, *Cucurbita moschata*, and *Ipomoea batatas*). Optimal and absolute temperature bounds (`topmn`, `topmx`, `tmin`, `tmax`), rainfall thresholds (`ropmn`, `ropmx`, `rmin`, `rmax`), and growing cycle lengths (`gmin`, `gmax`) are cross-referenced against local climate observations and harvested plant structures (roots/tubers, foliage, and fruits).

### 3. Lunar Ephemerides & Phase Calendar — U.S. Naval Observatory (USNO)
- **File:** `data/calendario_lunar_usno.csv`
- **Official Source:** [USNO — Astronomical Applications Department (*Primary Phases of the Moon*)](https://aa.usno.navy.mil/data/MoonPhases).
- **ETL & Structuring Methodology:** Because the USNO portal publishes annual lunar phase tables as static HTML (*Universal Time — UTC*), all official primary phase timestamps (**New Moon, First Quarter, Full Moon, and Last Quarter** from November 2026 through November 2027) were extracted, normalized to **ISO-8601 UTC** (`YYYY-MM-DD HH:MM`), and structured into a tabular CSV file.
- **Astronomical Engine Integration:** Within `app.py`, the official USNO phase timestamps serve as reference anchors alongside continuous ephemeris calculations (`ephem`) to compute exact daily lunar illumination percentages and align sowing, pruning, and harvesting windows with regional agroecological practices across any target year.

---

## Repository Structure

```text
urutau-nasa-space-apps/
├── assets/
│   ├── icon_urutau.svg        # Vector icon mark
│   ├── logo_urutau.svg        # Primary horizontal brand logo
│   └── text_urutau.svg        # Wordmark SVG
├── data/
│   ├── nasa_power_jequitinhonha.csv
│   ├── ecocrop.parquet
│   └── calendario_lunar_usno.csv
├── app.py                     # Main Streamlit application & crop recommendation engine
├── requirements.txt           # Python dependencies
└── README.md
