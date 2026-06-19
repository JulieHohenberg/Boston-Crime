import base64
import io
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Boston Crime",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────

UCR_MAP = {
    "Part One": "Serious Crime",
    "Part Two": "Non-Violent Crime",
    "Part Three": "Non-Criminal",
    "Other": "Unclassified",
}
UCR_ORDER = ["Serious Crime", "Non-Violent Crime", "Non-Criminal", "Unclassified"]
UCR_COLORS = ["#e31a1c", "#f9a825", "#4daf4a", "#aaaaaa"]

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_TIME_BUCKET_HOURS = {
    "Morning (6am–11am)":    list(range(6, 12)),
    "Afternoon (12pm–5pm)":  list(range(12, 18)),
    "Evening (6pm–10pm)":    list(range(18, 23)),
    "Late Night (11pm–5am)": list(range(23, 24)) + list(range(0, 6)),
}

# ── Data ──────────────────────────────────────────────────────────────────────

_LOCAL_CSV = Path("eda/boston_crime_compiled.csv")
_GDRIVE_ID = "1LEs1-R34OPROD3jJXO-vstMDcFssNOui"


@st.cache_data
def load_data():
    if _LOCAL_CSV.exists():
        raw = pd.read_csv(_LOCAL_CSV, encoding="latin-1", low_memory=False)
    else:
        url = f"https://drive.google.com/uc?export=download&id={_GDRIVE_ID}"
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        raw = pd.read_csv(io.StringIO(r.content.decode("latin-1")), low_memory=False)
    raw["UCR_PART"] = raw["UCR_PART"].map(UCR_MAP).fillna("Unclassified")
    return raw


df_raw = load_data()

# ── Sidebar CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {background-color:#000 !important;}
    section[data-testid="stSidebar"] > div {background-color:#000 !important;}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {color:white !important;}
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        border-color: rgba(255,255,255,0.45) !important;
        background-color: #111 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="tag"] {background:white !important;}
    section[data-testid="stSidebar"] [data-baseweb="tag"] span {color:black !important;}
    section[data-testid="stSidebar"] [data-baseweb="select"] input {color:white !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar filters ───────────────────────────────────────────────────────────

st.sidebar.header("Filters")

years_all = sorted(df_raw["YEAR"].dropna().unique().astype(int).tolist())
sel_years = st.sidebar.multiselect("Year", years_all, default=years_all)

ucr_avail = [u for u in UCR_ORDER if u in df_raw["UCR_PART"].unique()]
sel_ucr = st.sidebar.multiselect("Severity", ucr_avail, default=ucr_avail)

offense_types_all = sorted(df_raw["OFFENSE_CODE_GROUP"].dropna().unique().tolist())
sel_offense = st.sidebar.multiselect("Offense Type", offense_types_all, default=offense_types_all)

df = df_raw[
    df_raw["YEAR"].isin(sel_years)
    & df_raw["UCR_PART"].isin(sel_ucr)
    & df_raw["OFFENSE_CODE_GROUP"].isin(sel_offense)
].copy()

ucr_scale = alt.Scale(domain=UCR_ORDER, range=UCR_COLORS)
ucr_color = alt.Color("UCR_PART:N", scale=ucr_scale, legend=alt.Legend(title="Severity"))

# ── Hero metrics ──────────────────────────────────────────────────────────────

_n = len(df)
_top_type = df["OFFENSE_CODE_GROUP"].value_counts().idxmax() if _n > 0 else "N/A"
_serious_pct = f"{(df['UCR_PART'] == 'Serious Crime').sum() / _n:.1%}" if _n > 0 else "0%"
_nonviolent_pct = f"{(df['UCR_PART'] == 'Non-Violent Crime').sum() / _n:.1%}" if _n > 0 else "0%"
_noncrim_pct = f"{(df['UCR_PART'] == 'Non-Criminal').sum() / _n:.1%}" if _n > 0 else "0%"

# ── Hero ──────────────────────────────────────────────────────────────────────

_hero_path = Path("assets/cop_background_faded.png")
if _hero_path.exists():
    _hero_b64 = base64.b64encode(_hero_path.read_bytes()).decode()
    _hero_bg = f'url("data:image/png;base64,{_hero_b64}") center / cover no-repeat'
else:
    _hero_bg = "linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%)"

st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{padding-top: 0 !important;}}
    .hero {{
        background: {_hero_bg};
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 3rem 2rem;
        margin: -1rem -1rem 0 -1rem;
        position: relative;
    }}
    .hero-overlay {{
        position: absolute;
        inset: 0;
        background: rgba(0,0,0,0.48);
    }}
    .hero-inner {{
        position: relative;
        z-index: 1;
        width: 100%;
        max-width: 900px;
    }}
    .hero-title {{
        color: white;
        font-size: 4rem;
        font-weight: 800;
        text-shadow: 0 2px 20px rgba(0,0,0,0.9);
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.02em;
    }}
    .hero-sub {{
        color: rgba(255,255,255,0.88);
        font-size: clamp(6.5rem, 12vw, 10rem);
        font-weight: 400;
        line-height: 1;
        text-shadow: 0 1px 8px rgba(0,0,0,0.7);
        margin: 0;
    }}
    .scroll-hint {{
        color: rgba(255,255,255,0.75);
        font-size: 2.2rem;
        animation: bounce 2s ease-in-out infinite;
        user-select: none;
    }}
    @keyframes bounce {{
        0%,100% {{ transform: translateY(0); }}
        50%      {{ transform: translateY(10px); }}
    }}
    </style>
    <div class="hero">
      <div class="hero-overlay"></div>
      <div class="hero-inner">
        <div class="hero-title">Boston Crime</div>
        <p class="hero-sub">Where, When, &amp; Why?</p>
      </div>
      <div style="position:absolute;bottom:2rem;left:50%;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;gap:0.15rem;z-index:1;">
        <span style="color:rgba(255,255,255,0.75);font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;text-shadow:0 1px 4px rgba(0,0,0,0.7);">Scroll</span>
        <div class="scroll-hint">&#8595;</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Metric cards ──────────────────────────────────────────────────────────────

_c = "flex:1;background:white;border-radius:10px;padding:1.2rem 1.5rem;box-shadow:0 2px 14px rgba(0,0,0,0.09);"
_l = "font-size:0.7rem;text-transform:uppercase;letter-spacing:0.09em;color:#718096;margin-bottom:0.35rem;"
_v = "font-size:2rem;font-weight:700;color:#1a202c;line-height:1.15;"
st.markdown(
    f"""
    <div style="display:flex;gap:1.2rem;padding:1.6rem 0 1.2rem 0;">
      <div style="{_c}border-top:3px solid #4a90d9;">
        <div style="{_l}">Incidents in View</div>
        <div style="{_v}">{_n:,}</div>
      </div>
      <div style="{_c}border-top:3px solid #4a90d9;">
        <div style="{_l}">Most Common Type</div>
        <div style="{_v};font-size:1.15rem;">{_top_type}</div>
      </div>
      <div style="{_c}border-top:3px solid #e31a1c;">
        <div style="{_l}">Serious Crime</div>
        <div style="{_v}">{_serious_pct}</div>
      </div>
      <div style="{_c}border-top:3px solid #f9a825;">
        <div style="{_l}">Non-Violent Crime</div>
        <div style="{_v}">{_nonviolent_pct}</div>
      </div>
      <div style="{_c}border-top:3px solid #4daf4a;">
        <div style="{_l}">Non-Criminal</div>
        <div style="{_v}">{_noncrim_pct}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Section 1: Monthly volume trend ──────────────────────────────────────────

st.markdown("## How did incident volume shift year to year?")
st.markdown(
    "Non-criminal calls (tows, medical assists, traffic stops) dominate every year. "
    "Hover a band for details. **Click a legend item** to isolate that severity."
)

monthly = df.groupby(["YEAR", "MONTH", "UCR_PART"]).size().reset_index(name="count")
monthly["date"] = pd.to_datetime(
    monthly["YEAR"].astype(str) + "-" + monthly["MONTH"].astype(str).str.zfill(2) + "-01"
)

area_sel = alt.selection_point(fields=["UCR_PART"], bind="legend")
area_color = alt.Color(
    "UCR_PART:N",
    scale=ucr_scale,
    legend=alt.Legend(
        title="Severity",
        labelFontSize=18,
        titleFontSize=18,
        labelOffset=2,
        titlePadding=6,
        symbolSize=280,
        direction="horizontal",
        orient="top",
        offset=4,
        padding=4,
    ),
)

area_chart = (
    alt.Chart(monthly)
    .mark_area(interpolate="monotone")
    .encode(
        x=alt.X("date:T", title="", axis=alt.Axis(format="%b %Y", labelAngle=-30, grid=False)),
        y=alt.Y("count:Q", stack=True, title="Incidents", axis=alt.Axis(grid=False)),
        color=area_color,
        order=alt.Order("UCR_PART:N", sort="ascending"),
        opacity=alt.condition(area_sel, alt.value(0.88), alt.value(0.1)),
        tooltip=[
            alt.Tooltip("date:T", title="Month", format="%B %Y"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .add_params(area_sel)
    .properties(height=340)
)

st.altair_chart(area_chart, use_container_width=True)

# ── Section 2: Time patterns ──────────────────────────────────────────────────

st.markdown("---")
st.markdown("## When does Boston stay busy?")
st.markdown(
    "Incidents peak in the late afternoon. "
    "**Click an hour bar** to filter the day-of-week breakdown to that hour. "
    "**Click a legend item** to isolate a severity in both charts."
)

hour_lbl_expr = (
    "datum.value == 0 ? '12 AM' : datum.value < 12 ? datum.value + ' AM' : "
    "datum.value == 12 ? '12 PM' : (datum.value - 12) + ' PM'"
)

hour_click = alt.selection_point(fields=["HOUR"])
legend_sel_2 = alt.selection_point(fields=["UCR_PART"], bind="legend")

df_time = df[["HOUR", "DAY_OF_WEEK", "UCR_PART"]].dropna().copy()

hour_bars = (
    alt.Chart(df_time)
    .mark_bar()
    .encode(
        x=alt.X("HOUR:O", title="Hour of Day",
                axis=alt.Axis(labelExpr=hour_lbl_expr, labelAngle=-45, grid=False)),
        y=alt.Y("count():Q", stack=True, title="Incidents", axis=alt.Axis(grid=False)),
        color=ucr_color,
        order=alt.Order("UCR_PART:N", sort="ascending"),
        opacity=alt.condition(legend_sel_2, alt.value(1.0), alt.value(0.1)),
        tooltip=[
            alt.Tooltip("HOUR:O", title="Hour"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count():Q", title="Incidents", format=","),
        ],
    )
    .add_params(hour_click, legend_sel_2)
    .properties(
        width=520, height=340,
        title=alt.TitleParams("Click an hour bar to filter the day chart", fontSize=12, color="#999"),
    )
)

dow_bars = (
    alt.Chart(df_time)
    .mark_bar()
    .encode(
        y=alt.Y("DAY_OF_WEEK:N", sort=DAY_ORDER, title="", axis=alt.Axis(grid=False)),
        x=alt.X("count():Q", stack=True, title="Incidents", axis=alt.Axis(grid=False)),
        color=ucr_color,
        order=alt.Order("UCR_PART:N", sort="ascending"),
        opacity=alt.condition(legend_sel_2, alt.value(1.0), alt.value(0.1)),
        tooltip=[
            alt.Tooltip("DAY_OF_WEEK:N", title="Day"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count():Q", title="Incidents", format=","),
        ],
    )
    .transform_filter(hour_click)
    .properties(
        width=400, height=340,
        title=alt.TitleParams(
            "Day-of-week breakdown for selected hour(s)", fontSize=12, color="#999"
        ),
    )
)

st.altair_chart(
    alt.hconcat(hour_bars, dow_bars, spacing=40).resolve_scale(color="shared"),
    use_container_width=True,
)

# ── Section 2b: What is happening, when? ──────────────────────────────────────

st.markdown("---")
st.markdown("## What is happening, when?")
st.markdown(
    "**Click a severity slice** to see when crimes of that severity occur, "
    "broken down by hour of day and day of week. No selection shows the overall pattern."
)

_severity_totals_hm = (
    df.groupby("UCR_PART")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
)
_severity_order_hm = _severity_totals_hm["UCR_PART"].tolist()
_df_hm_raw = df[df["HOUR"].notna() & df["DAY_OF_WEEK"].notna()][["UCR_PART", "HOUR", "DAY_OF_WEEK"]].copy()

severity_hm_sel = alt.selection_point(fields=["UCR_PART"], name="severity_hm_sel")

severity_hm_pie = (
    alt.Chart(_severity_totals_hm)
    .mark_arc(innerRadius=55, stroke="#fff", strokeWidth=1)
    .encode(
        theta=alt.Theta("count:Q", stack=True, title="Incidents"),
        color=alt.Color(
            "UCR_PART:N",
            scale=ucr_scale,
            legend=alt.Legend(
                title="Severity",
                labelFontSize=18,
                titleFontSize=18,
                labelOffset=2,
                titlePadding=6,
                symbolSize=280,
                direction="horizontal",
                orient="top",
                offset=4,
                padding=4,
            ),
        ),
        opacity=alt.condition(severity_hm_sel, alt.value(1.0), alt.value(0.35)),
        tooltip=[
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .add_params(severity_hm_sel)
    .properties(
        height=300,
        title=alt.TitleParams(
            "Click a severity slice to filter the heatmap below", fontSize=12, color="#999"
        ),
    )
)

type_hm_heat = (
    alt.Chart(_df_hm_raw)
    .mark_rect()
    .encode(
        x=alt.X(
            "HOUR:O",
            title="Hour of Day",
            axis=alt.Axis(labelExpr=hour_lbl_expr, labelAngle=-45, grid=False),
        ),
        y=alt.Y("DAY_OF_WEEK:N", sort=DAY_ORDER, title="", axis=alt.Axis(grid=False)),
        color=alt.Color(
            "count():Q",
            scale=alt.Scale(scheme="blues"),
            legend=alt.Legend(title="Incidents"),
        ),
        tooltip=[
            alt.Tooltip("HOUR:O", title="Hour"),
            alt.Tooltip("DAY_OF_WEEK:N", title="Day"),
            alt.Tooltip("count():Q", title="Incidents", format=","),
        ],
    )
    .transform_filter(severity_hm_sel)
    .properties(
        height=260,
        title=alt.TitleParams(
            "Incidents by hour of day × day of week", fontSize=12, color="#999"
        ),
    )
)

st.altair_chart(
    alt.vconcat(severity_hm_pie, type_hm_heat, spacing=30),
    use_container_width=True,
)

# ── Section 3: What is happening and is it changing? ─────────────────────────

st.markdown("---")
st.markdown("## What is happening, and is it changing?")
st.markdown(
    "**Click a bar** to highlight that offense type across both charts. "
    "Use **Offense Type** in the sidebar to narrow the list."
)

_EXCLUDE_OCG = {"Other"}

df_type_total = (
    df[~df["OFFENSE_CODE_GROUP"].isin(_EXCLUDE_OCG)]
    .groupby("OFFENSE_CODE_GROUP")
    .size()
    .reset_index(name="count")
)
_type_totals = df_type_total.set_index("OFFENSE_CODE_GROUP")["count"]
top15 = _type_totals.nlargest(15).index.tolist()
type_order = _type_totals.loc[top15].sort_values(ascending=False).index.tolist()
df_type_total = df_type_total[df_type_total["OFFENSE_CODE_GROUP"].isin(top15)]

df_year_type = (
    df[
        df["OFFENSE_CODE_GROUP"].isin(top15)
        & ~df["OFFENSE_CODE_GROUP"].isin(_EXCLUDE_OCG)
    ]
    .groupby(["OFFENSE_CODE_GROUP", "YEAR"])
    .size()
    .reset_index(name="count")
)

_offense_scale = alt.Scale(scheme="category20")
_offense_color_bar = alt.Color("OFFENSE_CODE_GROUP:N", scale=_offense_scale, legend=None)
_offense_color_leg = alt.Color(
    "OFFENSE_CODE_GROUP:N",
    scale=_offense_scale,
    legend=alt.Legend(title="Offense Type"),
)

type_bar_sel = alt.selection_point(fields=["OFFENSE_CODE_GROUP"])

type_bar = (
    alt.Chart(df_type_total)
    .mark_bar()
    .encode(
        y=alt.Y(
            "OFFENSE_CODE_GROUP:N",
            sort=type_order,
            title="",
            axis=alt.Axis(grid=False, labelLimit=400),
        ),
        x=alt.X("count:Q", title="Incidents", axis=alt.Axis(grid=False)),
        color=_offense_color_bar,
        opacity=alt.condition(type_bar_sel, alt.value(1.0), alt.value(0.2)),
        tooltip=[
            alt.Tooltip("OFFENSE_CODE_GROUP:N", title="Offense Type"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .add_params(type_bar_sel)
    .properties(
        width=600,
        height=480,
        title=alt.TitleParams("Click a bar to highlight →", fontSize=12, color="#999"),
    )
)

year_trend = (
    alt.Chart(df_year_type)
    .mark_line(point=alt.OverlayMarkDef(size=60), strokeWidth=2.5)
    .encode(
        x=alt.X("YEAR:O", title="Year", axis=alt.Axis(grid=False)),
        y=alt.Y("count:Q", title="Incidents", axis=alt.Axis(grid=False)),
        color=_offense_color_leg,
        opacity=alt.condition(type_bar_sel, alt.value(1.0), alt.value(0.05)),
        tooltip=[
            alt.Tooltip("YEAR:O", title="Year"),
            alt.Tooltip("OFFENSE_CODE_GROUP:N", title="Offense Type"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .properties(
        width=500,
        height=480,
        title=alt.TitleParams("Year over year trend by type", fontSize=12, color="#999"),
    )
)

st.altair_chart(
    alt.hconcat(type_bar, year_trend, spacing=50).resolve_scale(color="shared"),
    use_container_width=True,
)

# ── Section 4: Map ────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## Where does crime happen?")
st.markdown(
    "Use the **Year**, **Severity**, and **Offense Type** filters in the sidebar to control what appears on the map. "
    "Narrow by time of day or day of week below."
)

_all_buckets = list(_TIME_BUCKET_HOURS.keys())
_mc1, _mc2 = st.columns(2)
with _mc1:
    time_buckets = st.multiselect(
        "Time of Day", _all_buckets, default=_all_buckets, key="map_time"
    )
with _mc2:
    map_days = st.multiselect(
        "Day of Week", DAY_ORDER, default=DAY_ORDER, key="map_day"
    )

_sel_hours: list[int] = []
for _b in time_buckets:
    _sel_hours.extend(_TIME_BUCKET_HOURS[_b])

_UCR_RGB = {
    "Serious Crime":     [227, 26,  28],
    "Non-Violent Crime": [249, 168, 37],
    "Non-Criminal":      [77,  175, 74],
    "Unclassified":      [150, 150, 150],
}

_df_m = df[
    df["Lat"].notna()
    & df["Long"].notna()
    & (df["Lat"] != 0)
    & (df["Long"] != 0)
    & df["HOUR"].isin(_sel_hours)
    & df["DAY_OF_WEEK"].isin(map_days)
].copy()

_df_m["_r"] = _df_m["UCR_PART"].map(lambda x: _UCR_RGB.get(x, [150, 150, 150])[0])
_df_m["_g"] = _df_m["UCR_PART"].map(lambda x: _UCR_RGB.get(x, [150, 150, 150])[1])
_df_m["_b"] = _df_m["UCR_PART"].map(lambda x: _UCR_RGB.get(x, [150, 150, 150])[2])

_df_pdk = _df_m[[
    "Lat", "Long", "UCR_PART", "OFFENSE_DESCRIPTION",
    "neighborhood", "OCCURRED_ON_DATE", "_r", "_g", "_b",
]].reset_index(drop=True)

if len(_df_pdk) > 0:
    st.pydeck_chart(
        pdk.Deck(
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    _df_pdk,
                    get_position=["Long", "Lat"],
                    get_fill_color=["_r", "_g", "_b", 170],
                    get_radius=80,
                    radius_min_pixels=2,
                    radius_max_pixels=8,
                    pickable=True,
                )
            ],
            initial_view_state=pdk.ViewState(
                latitude=42.33, longitude=-71.07, zoom=11.5, pitch=0
            ),
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            tooltip={"text": "{OFFENSE_DESCRIPTION}\n{neighborhood}\n{OCCURRED_ON_DATE}"},
        ),
        use_container_width=True,
        height=540,
    )
    st.caption(f"Showing {len(_df_pdk):,} incidents")
else:
    st.info("No incidents match the current filters.")

# ── Section 5: Severity by neighborhood (top 12) ──────────────────────────────

st.markdown("---")
st.markdown("## How serious is crime by neighborhood?")
st.markdown(
    "Top 12 neighborhoods by total incident volume, sorted by serious crime count. "
    "**Click a legend item** to isolate a severity."
)

_TOP_N = 12

_top_nbhds = (
    df[df["neighborhood"].notna()]
    .groupby("neighborhood")
    .size()
    .nlargest(_TOP_N)
    .index.tolist()
)

nbhd_ucr = (
    df[df["neighborhood"].isin(_top_nbhds)]
    .groupby(["neighborhood", "UCR_PART"])
    .size()
    .reset_index(name="count")
)

_serious = nbhd_ucr[nbhd_ucr["UCR_PART"] == "Serious Crime"].set_index("neighborhood")["count"]
nbhd_order = _serious.reindex(_top_nbhds).sort_values(ascending=False).index.tolist()

nbhd_leg_sel = alt.selection_point(fields=["UCR_PART"], bind="legend")

severity_chart = (
    alt.Chart(nbhd_ucr)
    .mark_bar()
    .encode(
        x=alt.X(
            "neighborhood:N",
            sort=nbhd_order,
            title="",
            axis=alt.Axis(labelAngle=-40, grid=False),
        ),
        y=alt.Y("count:Q", stack=True, title="Incidents", axis=alt.Axis(grid=False)),
        color=alt.Color("UCR_PART:N", scale=ucr_scale, legend=alt.Legend(title="Severity")),
        order=alt.Order("UCR_PART:N", sort="ascending"),
        opacity=alt.condition(nbhd_leg_sel, alt.value(1.0), alt.value(0.1)),
        tooltip=[
            alt.Tooltip("neighborhood:N", title="Neighborhood"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .add_params(nbhd_leg_sel)
    .properties(height=360)
)

st.altair_chart(severity_chart, use_container_width=True)

# ── Section 6: Demographics ───────────────────────────────────────────────────

st.markdown("---")
st.markdown("## Does demographics predict crime?")
st.markdown(
    "Bubble size = population. **Click a bubble** to see that neighborhood's severity and offense type breakdown."
)

DEMO_CONFIGS = [
    ("median_hh_income",   "Median Household Income", "$,.0f"),
    ("poverty_rate",       "Poverty Rate",             ".1%"),
    ("pct_bachelors_plus", "% Bachelor's Degree+",    ".1%"),
    ("pct_less_than_hs",   "% Less than High School", ".1%"),
    ("pct_white",          "% White",                 ".1%"),
    ("pct_black",          "% Black",                 ".1%"),
    ("pct_hispanic",       "% Hispanic",              ".1%"),
    ("median_age",         "Median Age",              ".1f"),
]

demo_choice = st.selectbox(
    "Demographic variable",
    [lbl for _, lbl, _ in DEMO_CONFIGS],
    key="demo_choice",
)
demo_col_name, demo_label, demo_fmt = next(
    (c, l, f) for c, l, f in DEMO_CONFIGS if l == demo_choice
)


def _first_mode(s):
    m = s.dropna().mode()
    return m.iloc[0] if len(m) > 0 else None


_grp = df[df["neighborhood"].notna()].groupby("neighborhood")
nbhd_demo = _grp["INCIDENT_NUMBER"].count().rename("crime_count").reset_index()
nbhd_demo["total_pop"] = _grp["total_pop"].agg(_first_mode).values
for _dc, _, _ in DEMO_CONFIGS:
    if _dc in df.columns:
        nbhd_demo[_dc] = _grp[_dc].agg(_first_mode).values

nbhd_demo["crime_rate_per_1k"] = nbhd_demo["crime_count"] / nbhd_demo["total_pop"] * 1000
nbhd_demo = nbhd_demo.dropna(subset=[demo_col_name, "crime_rate_per_1k", "total_pop"])

_bubble_zoom = alt.selection_interval(bind="scales")

bubble_pts = (
    alt.Chart(nbhd_demo)
    .mark_circle(stroke="#fff", strokeWidth=1.5)
    .encode(
        x=alt.X(
            f"{demo_col_name}:Q",
            title=demo_label,
            axis=alt.Axis(format=demo_fmt, grid=False),
        ),
        y=alt.Y(
            "crime_rate_per_1k:Q",
            title="Incidents / 1,000 residents",
            axis=alt.Axis(grid=False),
        ),
        size=alt.Size(
            "total_pop:Q",
            scale=alt.Scale(range=[60, 1800]),
            legend=alt.Legend(title="Population", format=","),
        ),
        color=alt.Color(
            "crime_rate_per_1k:Q",
            scale=alt.Scale(scheme="reds"),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("neighborhood:N", title="Neighborhood"),
            alt.Tooltip(f"{demo_col_name}:Q", title=demo_label, format=demo_fmt),
            alt.Tooltip("crime_rate_per_1k:Q", title="Incidents / 1k", format=".1f"),
            alt.Tooltip("total_pop:Q", title="Population", format=","),
        ],
    )
    .add_params(_bubble_zoom)
)

bubble_lbl = (
    alt.Chart(nbhd_demo)
    .mark_text(align="left", dx=7, dy=-3, fontSize=12, color="#555")
    .encode(
        x=alt.X(f"{demo_col_name}:Q"),
        y=alt.Y("crime_rate_per_1k:Q"),
        text=alt.Text("neighborhood:N"),
    )
)

bubble_chart = (bubble_pts + bubble_lbl).properties(
    height=500,
    title=f"{demo_label} vs. Crime Rate by Neighborhood",
)

st.altair_chart(bubble_chart, use_container_width=True)
