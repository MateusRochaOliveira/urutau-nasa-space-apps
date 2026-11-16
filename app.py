import os
from datetime import date, datetime, timezone
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import ephem
import streamlit as st

st.set_page_config(page_title="URUTAU | Smart Planting Calendar", page_icon="🦉", layout="wide")

CROPS_META = {
    "Zea mays": ("Corn (Milho)", "grain", "First Quarter"),
    "Phaseolus vulgaris": ("Common Bean (Feijão)", "grain", "First Quarter"),
    "Manihot esculenta": ("Cassava (Mandioca)", "root", "New Moon"),
    "Sorghum bicolor": ("Sorghum (Sorgo)", "grain", "Last Quarter"),
    "Vigna unguiculata": ("Cowpea (Feijão-de-corda)", "grain", "First Quarter"),
    "Cucurbita moschata": ("Pumpkin (Abóbora)", "fruit", "First Quarter"),
    "Ipomoea batatas": ("Sweet Potato (Batata-doce)", "root", "New Moon"),
}

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    with open("data/nasa_power_jequitinhonha.csv", "r", encoding="utf-8") as f:
        skip = next((i + 1 for i, line in enumerate(f) if "-END HEADER-" in line), 0)
    df_clima = pd.read_csv("data/nasa_power_jequitinhonha.csv", skiprows=skip)
    df_clima.columns = [c.strip().upper() for c in df_clima.columns]
    df_clima.replace(-999, np.nan, inplace=True)
    df_clima["DATE"] = pd.to_datetime(
        df_clima["YEAR"].astype(int).astype(str) + df_clima["DOY"].astype(int).astype(str).str.zfill(3),
        format="%Y%j",
    )
    if "T2M_MAX" not in df_clima.columns:
        df_clima["T2M_MAX"] = df_clima["T2M"] + 5.5
    if "T2M_MIN" not in df_clima.columns:
        df_clima["T2M_MIN"] = df_clima["T2M"] - 5.5
    df_clima["DOY_NUM"] = df_clima["DATE"].dt.dayofyear
    df_clima["RAIN_7D"] = df_clima["PRECTOTCORR"].rolling(7, min_periods=1).sum()

    df_eco = pd.read_parquet("data/ecocrop.parquet")
    df_eco = df_eco[df_eco["scientificname"].isin(CROPS_META.keys())].drop_duplicates("scientificname").copy()
    return df_clima, df_eco


def get_moon_info(selected_date: date):
    obs = ephem.Date(datetime(selected_date.year, selected_date.month, selected_date.day, 12, 0, tzinfo=timezone.utc))
    illum = float(ephem.Moon(obs).phase)
    prev_new = ephem.previous_new_moon(obs)
    next_new = ephem.next_new_moon(obs)
    frac = float(obs - prev_new) / float(next_new - prev_new)

    if frac < 0.125 or frac >= 0.875:
        return "New Moon", "🌑 New Moon", illum, "Ideal for root crops (cassava, sweet potato) and soil preparation."
    elif frac < 0.375:
        return "First Quarter", "🌓 First Quarter", illum, "Ideal for corn, beans, cowpea, and pumpkins (strong vegetative growth)."
    elif frac < 0.625:
        return "Full Moon", "🌕 Full Moon", illum, "Best for harvesting fruits and pest control; avoid heavy sowing."
    else:
        return "Last Quarter", "🌗 Last Quarter", illum, "Ideal for hardy, drought-tolerant crops (sorghum) and pruning."


def score_crop(row_eco, rain_7d: float, tmean: float, moon_key: str) -> tuple[str, str]:
    sci = row_eco["scientificname"]
    _, _, ideal_moon = CROPS_META[sci]
    opt_min = float(row_eco["topmn"]) if pd.notna(row_eco["topmn"]) else 18.0
    opt_max = float(row_eco["topmx"]) if pd.notna(row_eco["topmx"]) else 32.0
    rmin = float(row_eco["rmin"]) if pd.notna(row_eco["rmin"]) else 400.0

    # Hardy semi-arid crops tolerate lower initial moisture
    min_rain_needed = 8.0 if rmin <= 550 else 15.0
    temp_ok = (opt_min - 2.0) <= tmean <= (opt_max + 2.0)
    lunar_bonus = " + 🌙 Lunar Match" if moon_key == ideal_moon else ""

    if rain_7d >= min_rain_needed and temp_ok:
        return "✅ Recommended Now", f"Good moisture ({rain_7d:.1f} mm) & thermal fit ({opt_min:.0f}–{opt_max:.0f}°C){lunar_bonus}"
    elif (rain_7d >= min_rain_needed * 0.5 and temp_ok) or (rain_7d >= min_rain_needed):
        return "⚠️ Sow with Caution", f"Marginal rain ({rain_7d:.1f} mm) or temperature ({tmean:.1f}°C){lunar_bonus}"
    else:
        return "🛑 Wait / Avoid", f"Moisture deficit ({rain_7d:.1f} mm) or outside thermal range ({opt_min:.0f}–{opt_max:.0f}°C)"


# --- 2. INTERFACE ---
df_clima, df_eco = load_data()

if os.path.exists("assets/logo_urutau.svg"):
    st.sidebar.image("assets/logo_urutau.svg", use_container_width=True)

target_date = st.sidebar.date_input(
    "📅 Choose Planting Date (Any Year):",
    value=date.today(),
    min_value=date(2026, 1, 1),
    max_value=date(2035, 12, 31),
)
target_ts = pd.Timestamp(target_date)

# Exact date or seasonal DOY baseline for future years
match = df_clima[df_clima["DATE"] == target_ts]
if not match.empty:
    clima = match.iloc[0]
    history = df_clima[df_clima["DATE"] <= target_ts].tail(30).copy()
else:
    doy = min(target_ts.dayofyear, int(df_clima["DOY_NUM"].max()))
    clima = df_clima[df_clima["DOY_NUM"] == doy].iloc[0]
    history = df_clima[df_clima["DOY_NUM"] <= doy].tail(30).copy()
    history["DATE"] = pd.date_range(end=target_ts, periods=len(history), freq="D")

rain_7d = float(clima["RAIN_7D"])
tmean = float(clima["T2M"])
tmax = float(clima["T2M_MAX"])
tmin = float(clima["T2M_MIN"])
moon_key, moon_label, moon_illum, moon_tip = get_moon_info(target_date)

st.title("🦉 URUTAU — What & When to Plant")
st.caption(f"Araçuaí, MG (Jequitinhonha Valley) • Target Date: **{target_date.strftime('%Y-%m-%d')}** • NASA POWER + FAO EcoCrop + Ephem")

# Top KPIs
c1, c2, c3 = st.columns(3)
c1.metric("7-Day Rainfall", f"{rain_7d:.1f} mm")
c2.metric("Temperature (Mean | Min/Max)", f"{tmean:.1f}°C ({tmin:.0f}°/{tmax:.0f}°C)")
c3.metric("Lunar Phase", moon_label, f"{moon_illum:.0f}% illuminated")

st.info(f"**🌙 Lunar Guidance for {target_date.strftime('%b %d, %Y')}:** {moon_tip}")

# --- 3. CROP RECOMMENDATION RANKING FOR THIS DATE ---
st.subheader(f"🌱 Best Crops to Plant on {target_date.strftime('%B %d, %Y')}")

recs = []
for _, row in df_eco.iterrows():
    sci = row["scientificname"]
    common, _, ideal_moon = CROPS_META[sci]
    status, reason = score_crop(row, rain_7d, tmean, moon_key)
    recs.append({
        "Status": status,
        "Crop": f"{common} — {sci}",
        "Ideal Lunar Phase": ideal_moon,
        "Agronomic Reasoning": reason,
    })

df_recs = pd.DataFrame(recs).sort_values("Status")
st.dataframe(df_recs, use_container_width=True, hide_index=True)

# --- 4. CLIMATE CONTEXT CHART ---
fig = go.Figure()
fig.add_trace(go.Bar(x=history["DATE"], y=history["PRECTOTCORR"], name="Daily Rain (mm)", marker_color="#1E88E5"))
fig.add_trace(go.Scatter(x=history["DATE"], y=history["T2M"], name="Mean Temp (°C)", yaxis="y2", line=dict(color="#E53935", width=2)))
fig.update_layout(
    title=f"30-Day Rainfall & Temperature Context ({target_date.year})",
    yaxis=dict(title="Rainfall (mm)"),
    yaxis2=dict(title="Temp (°C)", overlaying="y", side="right"),
    height=320,
    margin=dict(l=10, r=10, t=40, b=10),
)
st.plotly_chart(fig, use_container_width=True)
