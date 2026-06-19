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

# ── Constants ─────────────────────────────────────────────────────────────────

UCR_MAP = {
    "Part One": "Serious Crime",
    "Part Two": "Non-Violent Crime",
    "Part Three": "Non-Criminal",
    "Other": "Unclassified",
}
UCR_ORDER = ["Serious Crime", "Non-Violent Crime", "Non-Criminal", "Unclassified"]
# Red → yellow → green → gray
UCR_COLORS = ["#e31a1c", "#f9a825", "#4daf4a", "#aaaaaa"]

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_data
def load_data():
    df = pd.read_csv("eda/boston_crime_compiled.csv", encoding="latin-1", low_memory=False)
    df["UCR_PART"] = df["UCR_PART"].map(UCR_MAP).fillna("Unclassified")
    return df

df_raw = load_data()

# ── Sidebar filters (defined early so metrics can reference df) ───────────────

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

# ── Hero metrics (computed from filtered df) ──────────────────────────────────

_n = len(df)
_top_type = df["OFFENSE_CODE_GROUP"].value_counts().idxmax() if _n > 0 else "N/A"
_serious_pct = f"{(df['UCR_PART'] == 'Serious Crime').sum() / _n:.1%}" if _n > 0 else "0%"
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
        justify-content: flex-end;
        text-align: center;
        padding: 3rem 2rem 10vh 2rem;
        margin: -1rem -1rem 2rem -1rem;
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
        color: rgba(255,255,255,0.82);
        font-size: 1.2rem;
        font-weight: 400;
        text-shadow: 0 1px 8px rgba(0,0,0,0.7);
        margin: 0 0 3.5rem 0;
    }}
    .hero-stats {{
        display: flex;
        justify-content: center;
        gap: 5rem;
        margin-bottom: 4rem;
    }}
    .hero-stat {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.3rem;
    }}
    .hero-stat-val {{
        color: white;
        font-size: 2.4rem;
        font-weight: 700;
        line-height: 1;
        text-shadow: 0 2px 10px rgba(0,0,0,0.8);
    }}
    .hero-stat-lbl {{
        color: rgba(255,255,255,0.7);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        text-shadow: 0 1px 4px rgba(0,0,0,0.7);
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
        <p class="hero-sub">Exploring patterns, places, and people behind the data</p>
        <div class="hero-stats">
          <div class="hero-stat">
            <div class="hero-stat-lbl">Incidents in View</div>
            <div class="hero-stat-val">{_n:,}</div>
          </div>
          <div class="hero-stat">
            <div class="hero-stat-lbl">Most Common Type</div>
            <div class="hero-stat-val">{_top_type}</div>
          </div>
          <div class="hero-stat">
            <div class="hero-stat-lbl">Serious Crime</div>
            <div class="hero-stat-val">{_serious_pct}</div>
          </div>
          <div class="hero-stat">
            <div class="hero-stat-lbl">Non-Criminal</div>
            <div class="hero-stat-val">{_noncrim_pct}</div>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:0.15rem;">
          <span style="color:rgba(255,255,255,0.75);font-size:0.78rem;text-transform:uppercase;letter-spacing:0.12em;text-shadow:0 1px 4px rgba(0,0,0,0.7);">Scroll</span>
          <div class="scroll-hint">&#8595;</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Section 1: Monthly volume trend ──────────────────────────────────────────

st.markdown("## How did incident volume shift year to year?")
st.markdown(
    "Non-criminal calls (tows, medical assists, traffic stops) dominate every year. "
    "Hover a band for details. Click a legend item to isolate that severity."
)

monthly = (
    df.groupby(["YEAR", "MONTH", "UCR_PART"])
    .size()
    .reset_index(name="count")
)
monthly["date"] = pd.to_datetime(
    monthly["YEAR"].astype(str) + "-" + monthly["MONTH"].astype(str).str.zfill(2) + "-01"
)

area_sel = alt.selection_point(fields=["UCR_PART"], bind="legend")

area_chart = (
    alt.Chart(monthly)
    .mark_area(interpolate="monotone")
    .encode(
        x=alt.X(
            "date:T",
            title="",
            axis=alt.Axis(format="%b %Y", labelAngle=-30, grid=False),
        ),
        y=alt.Y("count:Q", stack=True, title="Incidents", axis=alt.Axis(grid=False)),
        color=ucr_color,
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
    "Incidents climb through the day and peak in the late afternoon. "
    "**Drag across the hour chart** to filter the day-of-week breakdown on the right. "
    "Click a legend item to isolate a severity in both charts."
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
    .add_params(brush, legend_sel_2)
    .properties(
        width=520,
        height=340,
        title=alt.TitleParams("Drag to select a time window", fontSize=12, color="#999"),
    )
)

dow_bars = (
    alt.Chart(df_time)
    .mark_bar()
    .encode(
        y=alt.Y(
            "DAY_OF_WEEK:N",
            sort=DAY_ORDER,
            title="",
            axis=alt.Axis(grid=False),
        ),
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
    .transform_filter(brush)
    .properties(
        width=400,
        height=340,
        title=alt.TitleParams(
            "Day-of-week breakdown (filtered by selected hours)", fontSize=12, color="#999"
        ),
    )
)

st.altair_chart(
    alt.hconcat(hour_bars, dow_bars, spacing=40).resolve_scale(color="shared"),
    use_container_width=True,
)

# ── Section 3: What is happening and is it changing? ─────────────────────────

st.markdown("---")
st.markdown("## What is happening, and is it changing?")
st.markdown(
    "Click an offense type to see how its severity mix has shifted year over year. "
    "Use **Offense Type** in the sidebar to narrow the list."
)

df_type_sev = (
    df.groupby(["OFFENSE_CODE_GROUP", "UCR_PART"])
    .size()
    .reset_index(name="count")
)
_type_totals = df_type_sev.groupby("OFFENSE_CODE_GROUP")["count"].sum()
top15 = _type_totals.nlargest(15).index.tolist()
type_order = _type_totals.loc[top15].sort_values().index.tolist()
df_type_sev = df_type_sev[
    df_type_sev["OFFENSE_CODE_GROUP"].isin(top15)
    & (df_type_sev["UCR_PART"] != "Unclassified")
]

df_year_sev = (
    df[df["OFFENSE_CODE_GROUP"].isin(top15)]
    .groupby(["OFFENSE_CODE_GROUP", "YEAR", "UCR_PART"])
    .size()
    .reset_index(name="count")
)
df_year_sev = df_year_sev[df_year_sev["UCR_PART"] != "Unclassified"]

_n_all_off = len(offense_types_all)
_n_sel_off = len(sel_offense)
_ps = "display:inline-block;background:#2c5282;color:white;padding:2px 9px;border-radius:12px;font-size:11px;margin:2px 3px;"
if _n_sel_off == _n_all_off:
    _pills_html = f'<span style="{_ps.replace("#2c5282","#276749")}">All {_n_all_off} offense types</span>'
elif _n_sel_off == 0:
    _pills_html = '<span style="color:#888;font-size:12px;">No offense types selected</span>'
elif _n_sel_off <= 8:
    _pills_html = " ".join(f'<span style="{_ps}">{t}</span>' for t in sorted(sel_offense))
else:
    _shown_off = sorted(sel_offense)[:6]
    _more_off = _n_sel_off - 6
    _pills_html = " ".join(f'<span style="{_ps}">{t}</span>' for t in _shown_off)
    _pills_html += f' <span style="display:inline-block;background:#555;color:white;padding:2px 9px;border-radius:12px;font-size:11px;margin:2px 3px;">+{_more_off} more</span>'
st.markdown(f'<div style="margin:0.4rem 0 1rem 0;">{_pills_html}</div>', unsafe_allow_html=True)

type_sel = alt.selection_point(fields=["OFFENSE_CODE_GROUP"])
legend_sel_3 = alt.selection_point(fields=["UCR_PART"], bind="legend")

type_bar = (
    alt.Chart(df_type_sev)
    .mark_bar()
    .encode(
        y=alt.Y(
            "OFFENSE_CODE_GROUP:N",
            sort=type_order,
            title="",
            axis=alt.Axis(grid=False),
        ),
        x=alt.X("count:Q", stack=True, title="Incidents", axis=alt.Axis(grid=False)),
        color=ucr_color,
        order=alt.Order("UCR_PART:N", sort="ascending"),
        opacity=alt.condition(legend_sel_3, alt.value(1.0), alt.value(0.1)),
        tooltip=[
            alt.Tooltip("OFFENSE_CODE_GROUP:N", title="Offense Type"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .add_params(type_sel, legend_sel_3)
    .properties(
        width=380,
        height=400,
        title=alt.TitleParams("Click to filter trend", fontSize=12, color="#999"),
    )
)

year_trend = (
    alt.Chart(df_year_sev)
    .mark_line(point=alt.OverlayMarkDef(size=60), strokeWidth=2.5)
    .encode(
        x=alt.X("YEAR:O", title="Year", axis=alt.Axis(grid=False)),
        y=alt.Y("sum(count):Q", title="Incidents", axis=alt.Axis(grid=False)),
        color=ucr_color,
        opacity=alt.condition(legend_sel_3, alt.value(1.0), alt.value(0.1)),
        tooltip=[
            alt.Tooltip("YEAR:O", title="Year"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("sum(count):Q", title="Incidents", format=","),
        ],
    )
    .transform_filter(type_sel)
    .properties(
        width=440,
        height=400,
        title=alt.TitleParams(
            "Year over year trend for selected type", fontSize=12, color="#999"
        ),
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
    "Use the **Year**, **Severity**, and **Offense Type** filters in the sidebar to control what appears on the map."
)

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
].copy()

_df_m["_r"] = _df_m["UCR_PART"].map(lambda x: _UCR_RGB.get(x, [150,150,150])[0])
_df_m["_g"] = _df_m["UCR_PART"].map(lambda x: _UCR_RGB.get(x, [150,150,150])[1])
_df_m["_b"] = _df_m["UCR_PART"].map(lambda x: _UCR_RGB.get(x, [150,150,150])[2])

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
    st.info("No incidents match the current sidebar filters.")

# ── Section 5: Severity by neighborhood (top 12) ──────────────────────────────

st.markdown("---")
st.markdown("## How serious is crime by neighborhood?")
st.markdown("Top 12 neighborhoods by total incident volume, sorted by serious crime count.")

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

_serious = (
    nbhd_ucr[nbhd_ucr["UCR_PART"] == "Serious Crime"]
    .set_index("neighborhood")["count"]
)
nbhd_order = _serious.reindex(_top_nbhds).sort_values(ascending=False).index.tolist()

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
        tooltip=[
            alt.Tooltip("neighborhood:N", title="Neighborhood"),
            alt.Tooltip("UCR_PART:N", title="Severity"),
            alt.Tooltip("count:Q", title="Incidents", format=","),
        ],
    )
    .properties(height=360)
)

st.altair_chart(severity_chart, use_container_width=True)

# ── Section 6: Demographics ───────────────────────────────────────────────────

st.markdown("---")
st.markdown("## Does demographics predict crime?")
st.markdown(
    "Explore how neighborhood characteristics relate to crime rates. "
    "Bubble size = population. Click a bubble to highlight that neighborhood."
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

nbhd_sel = alt.selection_point(fields=["neighborhood"])

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
        size=alt.Size("total_pop:Q", scale=alt.Scale(range=[60, 1800]), legend=None),
        color=alt.condition(
            nbhd_sel,
            alt.Color("crime_rate_per_1k:Q", scale=alt.Scale(scheme="reds"), legend=None),
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

bubble_lbl = (
    alt.Chart(nbhd_demo)
    .mark_text(align="left", dx=7, dy=-3, fontSize=10, color="#555")
    .encode(
        x=alt.X(f"{demo_col_name}:Q"),
        y=alt.Y("crime_rate_per_1k:Q"),
        text=alt.Text("neighborhood:N"),
        opacity=alt.condition(nbhd_sel, alt.value(0.85), alt.value(0.18)),
    )
)

st.altair_chart(
    (bubble_pts + bubble_lbl).properties(
        height=460,
        title=f"{demo_label} vs. Crime Rate by Neighborhood",
    ),
    use_container_width=True,
)
