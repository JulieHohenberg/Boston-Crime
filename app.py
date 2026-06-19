import base64
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Boston Crime",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Hero ──────────────────────────────────────────────────────────────────────

_hero_path = Path("assets/cop_background_faded.png")
if _hero_path.exists():
    _hero_b64 = base64.b64encode(_hero_path.read_bytes()).decode()
    _hero_css = f'url("data:image/png;base64,{_hero_b64}") center / cover no-repeat'
else:
    _hero_css = "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)"

st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{padding-top: 0 !important;}}
    .hero-section {{
        background: {_hero_css};
        min-height: 400px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 3rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
    }}
    .hero-title {{
        color: white;
        font-size: 3.5rem;
        font-weight: 800;
        text-shadow: 0 2px 16px rgba(0,0,0,0.85);
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }}
    .hero-sub {{
        color: rgba(255,255,255,0.88);
        font-size: 1.25rem;
        text-shadow: 0 1px 8px rgba(0,0,0,0.7);
        margin: 0;
        font-weight: 400;
    }}
    </style>
    <div class="hero-section">
        <div class="hero-title">Boston Crime</div>
        <p class="hero-sub">Exploring patterns, places, and people behind the data</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Constants ─────────────────────────────────────────────────────────────────

UCR_MAP = {
    "Part One": "Serious Crime",
    "Part Two": "Non-Violent Crime",
    "Part Three": "Non-Criminal",
    "Other": "Unclassified",
}
UCR_ORDER = ["Serious Crime", "Non-Violent Crime", "Non-Criminal", "Unclassified"]
UCR_COLORS = ["#d73027", "#fc8d59", "#fee090", "#aaaaaa"]

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    df = pd.read_csv("eda/boston_crime_compiled.csv", encoding="latin-1", low_memory=False)
    df["UCR_PART"] = df["UCR_PART"].map(UCR_MAP).fillna("Unclassified")
    return df

df_raw = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────

st.sidebar.header("Filters")

years_all = sorted(df_raw["YEAR"].dropna().unique().astype(int).tolist())
sel_years = st.sidebar.multiselect("Year", years_all, default=years_all)

ucr_avail = [u for u in UCR_ORDER if u in df_raw["UCR_PART"].unique()]
sel_ucr = st.sidebar.multiselect("Severity", ucr_avail, default=ucr_avail)

df = df_raw[df_raw["YEAR"].isin(sel_years) & df_raw["UCR_PART"].isin(sel_ucr)].copy()

ucr_scale = alt.Scale(domain=UCR_ORDER, range=UCR_COLORS)
ucr_color = alt.Color(
    "UCR_PART:N", scale=ucr_scale, legend=alt.Legend(title="Severity")
)

# ── Section 1: Big picture ────────────────────────────────────────────────────

st.markdown("## What is happening overall?")

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("Total Incidents", f"{len(df):,}")
with m2:
    st.metric("Shooting Incidents", f"{df['SHOOTING'].eq('Y').sum():,}")
with m3:
    top_off = (
        df["OFFENSE_CODE_GROUP"].value_counts().idxmax() if len(df) else "N/A"
    )
    st.metric("Top Offense", top_off)
with m4:
    top_nbhd = (
        df["neighborhood"].value_counts().idxmax()
        if df["neighborhood"].notna().any()
        else "N/A"
    )
    st.metric("Most Active Neighborhood", top_nbhd)
with m5:
    top_yr = str(int(df["YEAR"].value_counts().idxmax())) if len(df) else "N/A"
    st.metric("Most Active Year", top_yr)

# ── Section 2: Time patterns ──────────────────────────────────────────────────

st.markdown("---")
st.markdown("## When does Boston stay busy?")
st.markdown(
    "Incidents broken down by hour of day and day of week. "
    "Drag on the hour chart to filter the day chart by time window."
)

hour_lbl_expr = (
    "datum.value == 0 ? '12 AM' : datum.value < 12 ? datum.value + ' AM' : "
    "datum.value == 12 ? '12 PM' : (datum.value - 12) + ' PM'"
)

brush = alt.selection_interval(encodings=["x"])
legend_sel_2 = alt.selection_point(fields=["UCR_PART"], bind="legend")

df_time = df[["HOUR", "DAY_OF_WEEK", "UCR_PART"]].dropna().copy()

hour_bars = (
    alt.Chart(df_time)
    .mark_bar()
    .encode(
        x=alt.X(
            "HOUR:O",
            title="Hour of Day",
            axis=alt.Axis(labelExpr=hour_lbl_expr, labelAngle=-45, grid=False),
        ),
        y=alt.Y("count():Q", title="Incidents", axis=alt.Axis(grid=False)),
        color=alt.condition(brush, ucr_color, alt.value("#d0d0d0")),
        opacity=alt.condition(legend_sel_2, alt.value(1.0), alt.value(0.07)),
        tooltip=[
            alt.Tooltip("HOUR:O", title="Hour"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count():Q", title="Incidents", format=","),
        ],
    )
    .add_params(brush, legend_sel_2)
    .properties(
        width=600,
        height=300,
        title=alt.TitleParams("Drag to select a time window", fontSize=12, color="#999"),
    )
)

dow_bars = (
    alt.Chart(df_time)
    .mark_bar()
    .encode(
        x=alt.X(
            "DAY_OF_WEEK:N",
            sort=DAY_ORDER,
            title="Day of Week",
            axis=alt.Axis(labelAngle=-30, grid=False),
        ),
        y=alt.Y("count():Q", title="Incidents", axis=alt.Axis(grid=False)),
        color=alt.condition(brush, ucr_color, alt.value("#d0d0d0")),
        opacity=alt.condition(legend_sel_2, alt.value(1.0), alt.value(0.07)),
        tooltip=[
            alt.Tooltip("DAY_OF_WEEK:N", title="Day"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count():Q", title="Incidents", format=","),
        ],
    )
    .transform_filter(brush)
    .properties(
        width=320,
        height=300,
        title=alt.TitleParams(
            "Distribution within selected hours", fontSize=12, color="#999"
        ),
    )
)

st.altair_chart(
    alt.hconcat(hour_bars, dow_bars, spacing=40).resolve_scale(color="shared"),
    use_container_width=False,
)

# ── Section 3: Offense types and trends ──────────────────────────────────────

st.markdown("---")
st.markdown("## What is happening, and is it changing?")
st.markdown("Click an offense type to explore its year-over-year trend.")

top_types = (
    df.groupby("OFFENSE_CODE_GROUP")
    .size()
    .reset_index(name="count")
    .nlargest(15, "count")
)
type_order = top_types.sort_values("count")["OFFENSE_CODE_GROUP"].tolist()

type_sel = alt.selection_point(fields=["OFFENSE_CODE_GROUP"])

type_bar = (
    alt.Chart(top_types)
    .mark_bar()
    .encode(
        y=alt.Y(
            "OFFENSE_CODE_GROUP:N",
            sort=type_order,
            title="",
            axis=alt.Axis(grid=False),
        ),
        x=alt.X("count:Q", title="Incidents", axis=alt.Axis(grid=False)),
        color=alt.condition(type_sel, alt.value("#1a6b9a"), alt.value("#d0d0d0")),
        tooltip=[
            alt.Tooltip("OFFENSE_CODE_GROUP:N", title="Offense Type"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .add_params(type_sel)
    .properties(
        width=400,
        height=380,
        title=alt.TitleParams("Click to filter trend", fontSize=12, color="#999"),
    )
)

df_type_year = (
    df.groupby(["OFFENSE_CODE_GROUP", "YEAR"])
    .size()
    .reset_index(name="count")
)

year_trend = (
    alt.Chart(df_type_year)
    .mark_line(point=True, strokeWidth=2.5)
    .encode(
        x=alt.X("YEAR:O", title="Year", axis=alt.Axis(grid=False)),
        y=alt.Y("count:Q", title="Incidents", axis=alt.Axis(grid=False)),
        color=alt.Color("OFFENSE_CODE_GROUP:N", legend=None),
        tooltip=[
            alt.Tooltip("OFFENSE_CODE_GROUP:N", title="Offense Type"),
            alt.Tooltip("YEAR:O", title="Year"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .transform_filter(type_sel)
    .properties(
        width=460,
        height=380,
        title=alt.TitleParams(
            "Year over year trend for selected type", fontSize=12, color="#999"
        ),
    )
)

st.altair_chart(
    alt.hconcat(type_bar, year_trend, spacing=50).resolve_scale(color="independent"),
    use_container_width=False,
)

# ── Section 4: Map ────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("## Where does crime happen?")
st.markdown(
    "Use the filters below to explore the geographic spread of crime across Boston. "
    "These filters are independent of the sidebar."
)

_mc1, _mc2, _mc3 = st.columns([1, 1, 2])
with _mc1:
    map_years = st.multiselect("Year", years_all, default=years_all, key="map_yr")
with _mc2:
    map_sev = st.multiselect("Severity", ucr_avail, default=ucr_avail, key="map_sev")
with _mc3:
    off_types_all = sorted(df_raw["OFFENSE_CODE_GROUP"].dropna().unique().tolist())
    map_types = st.multiselect(
        "Offense Type", off_types_all, default=off_types_all, key="map_typ"
    )

_UCR_RGB = {
    "Serious Crime": [215, 48, 39],
    "Non-Violent Crime": [252, 141, 89],
    "Non-Criminal": [215, 175, 0],
    "Unclassified": [150, 150, 150],
}

_df_map_raw = df_raw[
    df_raw["YEAR"].isin(map_years)
    & df_raw["UCR_PART"].isin(map_sev)
    & df_raw["OFFENSE_CODE_GROUP"].isin(map_types)
    & df_raw["Lat"].notna()
    & df_raw["Long"].notna()
    & (df_raw["Lat"] != 0)
    & (df_raw["Long"] != 0)
].copy()

_df_map_raw["_r"] = _df_map_raw["UCR_PART"].map(
    lambda x: _UCR_RGB.get(x, [150, 150, 150])[0]
)
_df_map_raw["_g"] = _df_map_raw["UCR_PART"].map(
    lambda x: _UCR_RGB.get(x, [150, 150, 150])[1]
)
_df_map_raw["_b"] = _df_map_raw["UCR_PART"].map(
    lambda x: _UCR_RGB.get(x, [150, 150, 150])[2]
)

_pdk_cols = [
    "Lat", "Long", "UCR_PART", "OFFENSE_DESCRIPTION",
    "neighborhood", "OCCURRED_ON_DATE", "_r", "_g", "_b",
]
_df_pdk = _df_map_raw[_pdk_cols].reset_index(drop=True)

map_layer = pdk.Layer(
    "ScatterplotLayer",
    _df_pdk,
    get_position=["Long", "Lat"],
    get_fill_color=["_r", "_g", "_b", 170],
    get_radius=80,
    radius_min_pixels=2,
    radius_max_pixels=8,
    pickable=True,
)

map_view = pdk.ViewState(latitude=42.33, longitude=-71.07, zoom=11.5, pitch=0)

st.pydeck_chart(
    pdk.Deck(
        layers=[map_layer],
        initial_view_state=map_view,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={
            "text": "{OFFENSE_DESCRIPTION}\n{neighborhood}\n{OCCURRED_ON_DATE}"
        },
    ),
    use_container_width=True,
    height=540,
)
st.caption(f"Showing {len(_df_pdk):,} incidents")

# ── Section 5: Severity by neighborhood ──────────────────────────────────────

st.markdown("---")
st.markdown("## How serious is crime by neighborhood?")
st.markdown(
    "Neighborhoods sorted left to right by number of serious (Part One) crimes."
)

nbhd_ucr = (
    df[df["neighborhood"].notna()]
    .groupby(["neighborhood", "UCR_PART"])
    .size()
    .reset_index(name="count")
)

_serious_counts = (
    nbhd_ucr[nbhd_ucr["UCR_PART"] == "Serious Crime"]
    .set_index("neighborhood")["count"]
)
nbhd_sev_order = _serious_counts.sort_values(ascending=False).index.tolist()
_extras = [n for n in nbhd_ucr["neighborhood"].unique() if n not in nbhd_sev_order]
nbhd_sev_order += _extras

severity_chart = (
    alt.Chart(nbhd_ucr)
    .mark_bar()
    .encode(
        x=alt.X(
            "neighborhood:N",
            sort=nbhd_sev_order,
            title="",
            axis=alt.Axis(labelAngle=-45, grid=False),
        ),
        y=alt.Y("count:Q", title="Incidents", axis=alt.Axis(grid=False)),
        color=alt.Color(
            "UCR_PART:N",
            scale=ucr_scale,
            legend=alt.Legend(title="Severity"),
        ),
        tooltip=[
            alt.Tooltip("neighborhood:N", title="Neighborhood"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .properties(
        height=380,
        title="Crime severity by neighborhood, sorted by serious crime",
    )
)

st.altair_chart(severity_chart, use_container_width=True)

# ── Section 6: Offense type heatmap ──────────────────────────────────────────

st.markdown("---")
st.markdown("## What types of incidents define each neighborhood?")

nbhd_type = (
    df[df["neighborhood"].notna()]
    .groupby(["neighborhood", "OFFENSE_CODE_GROUP"])
    .size()
    .reset_index(name="count")
)

heatmap = (
    alt.Chart(nbhd_type)
    .mark_rect(stroke="white", strokeWidth=0.5)
    .encode(
        x=alt.X(
            "OFFENSE_CODE_GROUP:N",
            title="Offense Type",
            axis=alt.Axis(labelAngle=-45, grid=False),
        ),
        y=alt.Y(
            "neighborhood:N",
            title="",
            sort=nbhd_sev_order,
            axis=alt.Axis(grid=False),
        ),
        color=alt.Color(
            "count:Q", scale=alt.Scale(scheme="blues"), title="Incidents"
        ),
        tooltip=[
            alt.Tooltip("neighborhood:N", title="Neighborhood"),
            alt.Tooltip("OFFENSE_CODE_GROUP:N", title="Offense Type"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .properties(height=560)
)

st.altair_chart(heatmap, use_container_width=True)

# ── Section 7: Demographics ───────────────────────────────────────────────────

st.markdown("---")
st.markdown("## Does demographics predict crime?")
st.markdown(
    "Explore how neighborhood characteristics relate to crime rates. "
    "Bubble size represents population. Click a bubble to highlight that neighborhood."
)

DEMO_CONFIGS = [
    ("median_hh_income",  "Median Household Income", "$,.0f"),
    ("poverty_rate",      "Poverty Rate",             ".1%"),
    ("pct_bachelors_plus","% Bachelor's Degree+",     ".1%"),
    ("pct_less_than_hs",  "% Less than High School",  ".1%"),
    ("pct_white",         "% White",                  ".1%"),
    ("pct_black",         "% Black",                  ".1%"),
    ("pct_hispanic",      "% Hispanic",               ".1%"),
    ("median_age",        "Median Age",               ".1f"),
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

_nbhd_grp = df[df["neighborhood"].notna()].groupby("neighborhood")
nbhd_demo = (
    _nbhd_grp["INCIDENT_NUMBER"].count().rename("crime_count").reset_index()
)
nbhd_demo["total_pop"] = _nbhd_grp["total_pop"].agg(_first_mode).values
for _dc, _, _ in DEMO_CONFIGS:
    if _dc in df.columns:
        nbhd_demo[_dc] = _nbhd_grp[_dc].agg(_first_mode).values

nbhd_demo["crime_rate_per_1k"] = (
    nbhd_demo["crime_count"] / nbhd_demo["total_pop"] * 1000
)
nbhd_demo = nbhd_demo.dropna(
    subset=[demo_col_name, "crime_rate_per_1k", "total_pop"]
)

nbhd_sel = alt.selection_point(fields=["neighborhood"])

bubble_points = (
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
            "total_pop:Q", scale=alt.Scale(range=[60, 1800]), legend=None
        ),
        color=alt.condition(
            nbhd_sel,
            alt.Color(
                "crime_rate_per_1k:Q",
                scale=alt.Scale(scheme="reds"),
                legend=None,
            ),
            alt.value("#d4d4d4"),
        ),
        opacity=alt.condition(nbhd_sel, alt.value(0.92), alt.value(0.35)),
        tooltip=[
            alt.Tooltip("neighborhood:N", title="Neighborhood"),
            alt.Tooltip(f"{demo_col_name}:Q", title=demo_label, format=demo_fmt),
            alt.Tooltip("crime_rate_per_1k:Q", title="Incidents / 1k", format=".1f"),
            alt.Tooltip("total_pop:Q", title="Population", format=","),
        ],
    )
    .add_params(nbhd_sel)
)

bubble_labels = (
    alt.Chart(nbhd_demo)
    .mark_text(align="left", dx=7, dy=-3, fontSize=10, color="#555")
    .encode(
        x=alt.X(f"{demo_col_name}:Q"),
        y=alt.Y("crime_rate_per_1k:Q"),
        text=alt.Text("neighborhood:N"),
        opacity=alt.condition(nbhd_sel, alt.value(0.85), alt.value(0.18)),
    )
)

demo_chart = (
    (bubble_points + bubble_labels)
    .properties(
        height=460,
        title=f"{demo_label} vs. Crime Rate by Neighborhood",
    )
)

st.altair_chart(demo_chart, use_container_width=True)
