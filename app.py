import streamlit as st
import pandas as pd

st.set_page_config(page_title="Boston Crime Dashboard", layout="wide")
st.title("Boston Crime Dashboard")

# ── URL helpers ──────────────────────────────────────────────────────────────────

CRIME_URL = "https://drive.google.com/uc?id=18JWRExaiRkPVQtZfs88f-fTqHPiI1p3_&export=download"
OFFENSE_CODES_URL = "https://drive.google.com/uc?id=1RoXGLR85jhnttDGUd0BAJD9xX6t22IsN&export=download"

def _gdx(file_id):
    return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"

SUMMARY_ROWS = {"United States", "Massachusetts", "Massachusets", "Boston"}


def _nbhd(df, col_names):
    """Rename columns and strip US/MA/Boston summary rows."""
    df = df.copy()
    df.columns = col_names
    df = df[~df["neighborhood"].isin(SUMMARY_ROWS)]
    df = df.dropna(subset=["neighborhood"])
    df["neighborhood"] = df["neighborhood"].astype(str).str.strip()
    return df.reset_index(drop=True)


# ── Crime loaders ────────────────────────────────────────────────────────────────

@st.cache_data
def load_crime():
    return pd.read_csv(CRIME_URL, encoding="latin-1")


@st.cache_data
def load_offense_codes():
    return pd.read_csv(OFFENSE_CODES_URL, encoding="latin-1")


# ── Census loaders ───────────────────────────────────────────────────────────────

@st.cache_data
def load_age():
    df = pd.read_excel(_gdx("1unTPjKhz7_FkCjhtURZ0Ja-n7YRBg__V"), header=0)
    return _nbhd(df, [
        "neighborhood", "total_pop", "median_age",
        "count_0to9", "pct_0to9", "count_10to19", "pct_10to19",
        "count_20to34", "pct_20to34", "count_35to54", "pct_35to54",
        "count_55to64", "pct_55to64", "count_65plus", "pct_65plus",
    ])


@st.cache_data
def load_education():
    df = pd.read_excel(_gdx("1isPtMf-mtfnt3wmb8-yYslGeZe3rjroL"), header=0)
    return _nbhd(df, [
        "neighborhood", "edu_pop_25plus",
        "count_less_than_hs", "pct_less_than_hs",
        "count_hs_grad", "pct_hs_grad",
        "count_some_college", "pct_some_college",
        "count_bachelors_plus", "pct_bachelors_plus",
    ])


@st.cache_data
def load_hh_income():
    df = pd.read_excel(_gdx("1MaZDSUw60OGHaJRstyA-q-fwKu-PBUdA"), header=0)
    return _nbhd(df, [
        "neighborhood", "median_hh_income", "total_hh",
        "count_under15k", "pct_under15k",
        "count_15k_25k", "pct_15k_25k",
        "count_25k_35k", "pct_25k_35k",
        "count_35k_50k", "pct_35k_50k",
        "count_50k_75k", "pct_50k_75k",
        "count_75k_100k", "pct_75k_100k",
        "count_100k_150k", "pct_100k_150k",
        "count_150k_plus", "pct_150k_plus",
    ])


@st.cache_data
def load_geo_mobility():
    df = pd.read_excel(_gdx("1WhArm_0RDeArrZzIxlqUPNw_8_5s65E7"), header=0)
    return _nbhd(df, [
        "neighborhood", "total_mobility",
        "count_same_house", "pct_same_house",
        "count_moved_same_county", "pct_moved_same_county",
        "count_moved_diff_county", "pct_moved_diff_county",
        "count_moved_diff_state", "pct_moved_diff_state",
        "count_moved_abroad", "pct_moved_abroad",
    ])


@st.cache_data
def load_group_quarters():
    df = pd.read_excel(_gdx("1F-QWD_kTl9PeYsyQIhUoZWXvLZLiZipB"), header=0)
    return _nbhd(df, ["neighborhood", "group_quarters_pop", "pct_group_quarters"])


@st.cache_data
def load_industries():
    df = pd.read_excel(_gdx("1F1HjR5hp5A5OD21bld9iVG6i4nQNNnvJ"), header=0)
    return _nbhd(df, [
        "neighborhood", "employed_pop",
        "count_finance", "pct_finance",
        "count_professional", "pct_professional",
        "count_arts_entertainment", "pct_arts_entertainment",
        "count_admin", "pct_admin",
        "count_food_accommodation", "pct_food_accommodation",
        "count_other_services", "pct_other_services",
        "count_education_industry", "pct_education_industry",
        "count_healthcare", "pct_healthcare",
        "count_construction_mfg", "pct_construction_mfg",
        "count_retail_wholesale", "pct_retail_wholesale",
    ])


@st.cache_data
def load_labor_force():
    # Cols 6-8 are empty trailing columns — drop them
    df = pd.read_excel(_gdx("1GhjntDa_2IgK5ddeC-lV3nThOQXFhdS_"), header=0, usecols=range(6))
    return _nbhd(df, [
        "neighborhood", "pop_16plus", "civilian_labor_force",
        "labor_force_participation_rate", "employed_civilians", "employment_rate",
    ])


@st.cache_data
def load_nativity():
    df = pd.read_excel(_gdx("1KccceUdTILgMRZr1GsSJB7EEaNyXbP_X"), header=0)
    return _nbhd(df, [
        "neighborhood", "total_nativity",
        "count_us_born", "pct_us_born",
        "count_born_pr_islands", "pct_born_pr_islands",
        "count_born_abroad_american_parents", "pct_born_abroad_american_parents",
        "count_naturalized", "pct_naturalized",
        "count_not_citizen", "pct_not_citizen",
    ])


@st.cache_data
def load_occupation():
    df = pd.read_excel(_gdx("1JMr-KKYJqXM5mrNqiZXKyUtFGIAW6Paa"), header=0)
    return _nbhd(df, [
        "neighborhood", "employed_pop",
        "count_mgmt_business", "pct_mgmt_business",
        "count_computer_engineering", "pct_computer_engineering",
        "count_education_legal_arts", "pct_education_legal_arts",
        "count_healthcare_practitioner", "pct_healthcare_practitioner",
        "count_service", "pct_service",
        "count_sales_office", "pct_sales_office",
        "count_natural_resources", "pct_natural_resources",
        "count_production_transport", "pct_production_transport",
    ])


@st.cache_data
def load_per_capita_income():
    df = pd.read_excel(_gdx("1qujXXIRzYkBspYS91KIhKA3p5MIqw8ru"), header=0)
    return _nbhd(df, ["neighborhood", "total_pop", "aggregate_income", "per_capita_income"])


@st.cache_data
def load_poverty_by_age():
    # Two header rows — skip both and assign names manually
    df = pd.read_excel(_gdx("1Mr1PBaXPtUUw9tB1a56TmXbtSJOElJQx"), header=None, skiprows=2)
    return _nbhd(df, [
        "neighborhood", "total_pop",
        "under18_total", "under18_poverty", "under18_poverty_rate",
        "age18to64_total", "age18to64_poverty", "age18to64_poverty_rate",
        "age65plus_total", "age65plus_poverty", "age65plus_poverty_rate",
    ])


@st.cache_data
def load_poverty():
    df = pd.read_excel(_gdx("1rwsuBjnQvK0faC5gKPJR1bXK3X2jqjaY"), header=0)
    return _nbhd(df, [
        "neighborhood", "total_pop_poverty_status",
        "total_in_poverty", "poverty_rate", "pct_boston_impoverished",
    ])


@st.cache_data
def load_race_ethnicity():
    df = pd.read_excel(_gdx("1VBNSoiOkzCnX4eNxSJFtw2IBIt3GUuF1"), header=0)
    return _nbhd(df, [
        "neighborhood", "total_pop",
        "count_white", "pct_white",
        "count_black", "pct_black",
        "count_hispanic", "pct_hispanic",
        "count_asian", "pct_asian",
        "count_other_races", "pct_other_races",
    ])


@st.cache_data
def load_school_enrollment():
    df = pd.read_excel(_gdx("1_0KiJ6B_uO2pNi4NOhw1CsOoE3CYaGzr"), header=0)
    return _nbhd(df, [
        "neighborhood", "pop_age3plus",
        "enrolled_total", "pct_enrolled",
        "count_preschool", "pct_preschool",
        "count_kindergarten", "pct_kindergarten",
        "count_grade1to4", "pct_grade1to4",
        "count_grade5to8", "pct_grade5to8",
        "count_grade9to12", "pct_grade9to12",
        "count_college_undergrad", "pct_college_undergrad",
        "count_grad_school", "pct_grad_school",
        "count_not_enrolled", "pct_not_enrolled",
    ])


@st.cache_data
def load_vehicles_per_hh():
    df = pd.read_excel(_gdx("1ZWhR44d56kG-1AlnbMYoGqML0cxFT_X2"), header=0)
    return _nbhd(df, [
        "neighborhood", "total_hh",
        "count_0_vehicles", "pct_0_vehicles",
        "count_1_vehicle", "pct_1_vehicle",
        "count_2_vehicles", "pct_2_vehicles",
        "count_3plus_vehicles", "pct_3plus_vehicles",
    ])


CENSUS_LOADERS = {
    "Age": load_age,
    "Educational Attainment": load_education,
    "Household Income": load_hh_income,
    "Geographic Mobility": load_geo_mobility,
    "Group Quarters": load_group_quarters,
    "Industries": load_industries,
    "Labor Force": load_labor_force,
    "Nativity": load_nativity,
    "Occupation": load_occupation,
    "Per Capita Income": load_per_capita_income,
    "Poverty by Age": load_poverty_by_age,
    "Poverty Rates": load_poverty,
    "Race & Ethnicity": load_race_ethnicity,
    "School Enrollment": load_school_enrollment,
    "Vehicles per Household": load_vehicles_per_hh,
}

# ── App tabs ─────────────────────────────────────────────────────────────────────

crime_tab, census_tab = st.tabs(["Crime Dashboard", "Census Data"])

# ── Crime tab ────────────────────────────────────────────────────────────────────

with crime_tab:
    try:
        crime = load_crime()
        st.success(f"crime.csv loaded — {len(crime):,} rows")
    except Exception as e:
        st.error(f"Could not load crime.csv: {e}")
        st.stop()

    try:
        offense_codes = load_offense_codes()
        st.success("offense_codes.csv loaded")
    except Exception as e:
        st.error(f"Could not load offense_codes.csv: {e}")
        st.stop()

    crime_code_col = next(
        (c for c in crime.columns if "offense_code" in c.lower() or c.lower() == "code"), None
    )
    offense_code_col = next(
        (c for c in offense_codes.columns if "code" in c.lower()), None
    )

    if crime_code_col and offense_code_col:
        merged = crime.merge(offense_codes, left_on=crime_code_col, right_on=offense_code_col, how="left")
    else:
        merged = crime.copy()

    # Sidebar filters
    st.sidebar.header("Crime Filters")

    year_col = next((c for c in merged.columns if c.upper() == "YEAR"), None)
    if year_col:
        years = sorted(merged[year_col].dropna().unique().tolist())
        selected_years = st.sidebar.multiselect("Year", options=years, default=years)
        merged = merged[merged[year_col].isin(selected_years)]

    district_col = next((c for c in merged.columns if c.upper() == "DISTRICT"), None)
    if district_col:
        districts = sorted(merged[district_col].dropna().unique().tolist())
        selected_districts = st.sidebar.multiselect("District", options=districts, default=districts)
        merged = merged[merged[district_col].isin(selected_districts)]

    desc_col = next(
        (c for c in merged.columns if "offense_description" in c.lower() or c.lower() == "offense_desc"), None
    )
    if not desc_col:
        desc_col = next(
            (c for c in merged.columns if c.upper() == "NAME" or "name" in c.lower()), None
        )

    if desc_col:
        descriptions = sorted(merged[desc_col].dropna().unique().tolist())
        selected_descs = st.sidebar.multiselect("Offense description", options=descriptions, default=descriptions)
        merged = merged[merged[desc_col].isin(selected_descs)]

    st.subheader(f"Filtered data — {len(merged):,} rows")
    st.dataframe(merged.head(50))

    st.subheader("Charts")

    if desc_col:
        st.write("Crime count by offense type (top 15)")
        offense_counts = (
            merged[desc_col].value_counts().head(15)
            .rename_axis("Offense").reset_index(name="Count")
        )
        st.bar_chart(offense_counts.set_index("Offense"))

    if district_col:
        st.write("Crime count by district")
        district_counts = (
            merged[district_col].value_counts()
            .rename_axis("District").reset_index(name="Count")
        )
        st.bar_chart(district_counts.set_index("District"))

    month_col = next((c for c in merged.columns if c.upper() == "MONTH"), None)
    if year_col and month_col:
        st.write("Crime count by year and month")
        merged["year_month"] = (
            merged[year_col].astype(str) + "-" + merged[month_col].astype(str).str.zfill(2)
        )
        time_counts = (
            merged["year_month"].value_counts().sort_index()
            .rename_axis("Year-Month").reset_index(name="Count")
        )
        st.line_chart(time_counts.set_index("Year-Month"))
    elif year_col:
        st.write("Crime count by year")
        year_counts = (
            merged[year_col].value_counts().sort_index()
            .rename_axis("Year").reset_index(name="Count")
        )
        st.bar_chart(year_counts.set_index("Year"))

# ── Census tab ───────────────────────────────────────────────────────────────────

with census_tab:
    census_tables = {}
    load_errors = []

    with st.spinner("Loading census tables..."):
        for name, loader in CENSUS_LOADERS.items():
            try:
                census_tables[name] = loader()
            except Exception as e:
                load_errors.append((name, str(e)))

    if load_errors:
        for name, err in load_errors:
            st.warning(f"{name} failed to load: {err}")

    st.success(f"Loaded {len(census_tables)}/{len(CENSUS_LOADERS)} census tables.")

    # Head preview of every table
    st.subheader("Table previews (first 3 rows each)")
    for name, df in census_tables.items():
        st.caption(f"**{name}** — {len(df)} neighborhoods, {df.shape[1]} cols")
        st.dataframe(df.head(3))

    # Full table explorer
    st.subheader("Explore a census table (full)")
    selected = st.selectbox("Table", options=list(census_tables.keys()))
    if selected:
        st.dataframe(census_tables[selected])

    # Neighborhood summary — key metrics merged into one table
    st.subheader("Neighborhood Summary (key metrics)")

    def _pick(table, cols):
        if table in census_tables:
            return census_tables[table][["neighborhood"] + cols]
        return None

    summary = _pick("Per Capita Income", ["total_pop", "per_capita_income"])
    for tbl, cols in [
        ("Household Income",        ["median_hh_income"]),
        ("Age",                     ["median_age"]),
        ("Poverty Rates",           ["poverty_rate"]),
        ("Educational Attainment",  ["pct_bachelors_plus", "pct_less_than_hs"]),
        ("Race & Ethnicity",        ["pct_white", "pct_black", "pct_hispanic", "pct_asian"]),
        ("Labor Force",             ["labor_force_participation_rate", "employment_rate"]),
        ("Vehicles per Household",  ["pct_0_vehicles"]),
        ("Nativity",                ["pct_not_citizen"]),
    ]:
        piece = _pick(tbl, cols)
        if piece is not None and summary is not None:
            summary = summary.merge(piece, on="neighborhood", how="left")

    if summary is not None:
        st.dataframe(summary.set_index("neighborhood"))

        col1, col2 = st.columns(2)
        with col1:
            st.write("Per capita income by neighborhood")
            st.bar_chart(summary.set_index("neighborhood")["per_capita_income"])
        with col2:
            st.write("Poverty rate by neighborhood")
            st.bar_chart(summary.set_index("neighborhood")["poverty_rate"])

        col3, col4 = st.columns(2)
        with col3:
            st.write("% Bachelor's degree or higher")
            st.bar_chart(summary.set_index("neighborhood")["pct_bachelors_plus"])
        with col4:
            st.write("Median age by neighborhood")
            st.bar_chart(summary.set_index("neighborhood")["median_age"])
