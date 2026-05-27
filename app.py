import streamlit as st
import pandas as pd

st.title("Boston Crime Dashboard")

# URLs for the two CSV files hosted on Google Drive
CRIME_URL = "https://drive.google.com/uc?id=18JWRExaiRkPVQtZfs88f-fTqHPiI1p3_&export=download"
OFFENSE_CODES_URL = "https://drive.google.com/uc?id=1RoXGLR85jhnttDGUd0BAJD9xX6t22IsN&export=download"


@st.cache_data
def load_crime():
    return pd.read_csv(CRIME_URL, encoding="latin-1")


@st.cache_data
def load_offense_codes():
    return pd.read_csv(OFFENSE_CODES_URL, encoding="latin-1")


# Load the data
st.subheader("Loading data...")

try:
    crime = load_crime()
    st.success("crime.csv loaded successfully.")
except Exception as e:
    st.error(f"Could not load crime.csv: {e}")
    st.stop()

try:
    offense_codes = load_offense_codes()
    st.success("offense_codes.csv loaded successfully.")
except Exception as e:
    st.error(f"Could not load offense_codes.csv: {e}")
    st.stop()


# Show column names for both datasets
st.subheader("Column names")
st.write("crime.csv columns:", list(crime.columns))
st.write("offense_codes.csv columns:", list(offense_codes.columns))


# Preview each dataset
st.subheader("Preview: crime.csv")
st.dataframe(crime.head())

st.subheader("Preview: offense_codes.csv")
st.dataframe(offense_codes.head())


# Try to merge on the offense code column
# Common column name candidates in Boston crime data
crime_code_col = None
offense_code_col = None

for col in crime.columns:
    if "offense_code" in col.lower() or col.lower() == "code":
        crime_code_col = col
        break

for col in offense_codes.columns:
    if "code" in col.lower():
        offense_code_col = col
        break

if crime_code_col and offense_code_col:
    st.subheader("Merged dataset")
    merged = crime.merge(offense_codes, left_on=crime_code_col, right_on=offense_code_col, how="left")
    st.write(f"Merged on crime column `{crime_code_col}` and offense_codes column `{offense_code_col}`.")
    st.dataframe(merged.head())
else:
    st.warning(
        "Could not automatically find matching columns to merge the two datasets. "
        f"crime.csv columns: {list(crime.columns)} | "
        f"offense_codes.csv columns: {list(offense_codes.columns)}"
    )
    merged = crime.copy()


# Sidebar filters
st.sidebar.header("Filters")

# Year filter
year_col = None
for col in merged.columns:
    if col.upper() == "YEAR" or col.lower() == "year":
        year_col = col
        break

if year_col:
    years = sorted(merged[year_col].dropna().unique().tolist())
    selected_years = st.sidebar.multiselect("Year", options=years, default=years)
    merged = merged[merged[year_col].isin(selected_years)]

# District filter
district_col = None
for col in merged.columns:
    if col.upper() == "DISTRICT" or col.lower() == "district":
        district_col = col
        break

if district_col:
    districts = sorted(merged[district_col].dropna().unique().tolist())
    selected_districts = st.sidebar.multiselect("District", options=districts, default=districts)
    merged = merged[merged[district_col].isin(selected_districts)]

# Offense description filter
desc_col = None
for col in merged.columns:
    if "offense_description" in col.lower() or col.lower() == "offense_desc":
        desc_col = col
        break

if not desc_col:
    # offense_codes.csv often has a NAME column for the description
    for col in merged.columns:
        if col.upper() == "NAME" or "name" in col.lower():
            desc_col = col
            break

if desc_col:
    descriptions = sorted(merged[desc_col].dropna().unique().tolist())
    selected_descs = st.sidebar.multiselect("Offense description", options=descriptions, default=descriptions)
    merged = merged[merged[desc_col].isin(selected_descs)]


st.subheader("Filtered data")
st.write(f"{len(merged)} rows after filters.")
st.dataframe(merged.head(50))


# Charts
st.subheader("Charts")

# Crime count by offense type
if desc_col and desc_col in merged.columns:
    st.write("Crime count by offense type (top 15)")
    offense_counts = (
        merged[desc_col]
        .value_counts()
        .head(15)
        .reset_index()
    )
    offense_counts.columns = ["Offense", "Count"]
    st.bar_chart(offense_counts.set_index("Offense"))

# Crime count by district
if district_col and district_col in merged.columns:
    st.write("Crime count by district")
    district_counts = (
        merged[district_col]
        .value_counts()
        .reset_index()
    )
    district_counts.columns = ["District", "Count"]
    st.bar_chart(district_counts.set_index("District"))

# Crime count over time
month_col = None
for col in merged.columns:
    if col.upper() == "MONTH" or col.lower() == "month":
        month_col = col
        break

if year_col and month_col:
    st.write("Crime count by year and month")
    merged["year_month"] = (
        merged[year_col].astype(str) + "-" + merged[month_col].astype(str).str.zfill(2)
    )
    time_counts = (
        merged["year_month"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    time_counts.columns = ["Year-Month", "Count"]
    st.line_chart(time_counts.set_index("Year-Month"))
elif year_col:
    st.write("Crime count by year")
    year_counts = (
        merged[year_col]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    year_counts.columns = ["Year", "Count"]
    st.bar_chart(year_counts.set_index("Year"))
