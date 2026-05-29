# Boston Crime Dashboard

Data visualization project exploring crime patterns in Boston (2015–2018) alongside neighborhood-level census data.

## Data Sources

**Crime data** — [Crimes in Boston, Kaggle (AnalyzeBoston)](https://www.kaggle.com/datasets/AnalyzeBoston/crimes-in-boston?resource=download)  
Incident-level crime records from the Boston Police Department, covering 2015–2018. Includes offense type, district, date/time, and lat/long. Licensed under [CC0: Public Domain](https://creativecommons.org/publicdomain/zero/1.0/).

| INCIDENT_NUMBER | OFFENSE_CODE | OFFENSE_CODE_GROUP | DISTRICT | OCCURRED_ON_DATE | Lat | Long |
|---|---|---|---|---|---|---|
| I182070945 | 619 | Larceny | D14 | 2018-09-02 13:00:00 | 42.357791 | -71.139371 |
| I182070943 | 1402 | Vandalism | C11 | 2018-08-21 00:00:00 | 42.306821 | -71.060300 |
| I182070941 | 3410 | Towed | D4 | 2018-09-03 19:27:00 | 42.346589 | -71.072429 |

**Neighborhood demographics** — [City of Boston Neighborhood Demographics, Analyze Boston](https://data.boston.gov/dataset/neighborhood-demographics/resource/e684798f-e175-4ab1-8f70-ed80e4e260cc)  
American Community Survey (ACS) 2013–2017 5-year estimates at the Boston neighborhood level. Licensed under [Open Data Commons PDDL](https://opendatacommons.org/licenses/pddl/).

The following census tables are used:

- Age distribution and median age
- Educational attainment
- Household income brackets and median income
- Geographic mobility
- Group quarters population
- Industry of employment
- Labor force participation and employment rate
- Nativity and citizenship status
- Occupation
- Per capita income
- Poverty rates (overall and by age group)
- Race and ethnicity
- School enrollment
- Vehicles per household

### Sample census tables

**Age distribution**

| neighborhood | total_pop | median_age | % age 20–34 | % age 65+ |
|---|---|---|---|---|
| Allston | 19,363 | 26 | 67.6% | 3.4% |
| Back Bay | 18,176 | 33 | 41.3% | 14.5% |
| Beacon Hill | 9,751 | 32 | 48.8% | 12.3% |

**Household income**

| neighborhood | median_hh_income | % under $15k | % $150k+ |
|---|---|---|---|
| Allston | $46,983 | 22.5% | 8.3% |
| Back Bay | $102,071 | 14.3% | 34.7% |
| Beacon Hill | $98,069 | 10.7% | 31.7% |

**Educational attainment** (residents 25+)

| neighborhood | % less than HS | % HS grad | % bachelor's+ |
|---|---|---|---|
| Allston | 6.8% | 9.3% | 71.9% |
| Back Bay | 2.3% | 4.9% | 85.0% |
| Beacon Hill | 2.3% | 2.2% | 89.8% |

## Data merge

Crime records use BPD district codes (e.g. D14, C11) while census data is organized by neighborhood. To join them, each crime record's lat/long is matched to a Boston neighborhood polygon using a point-in-polygon spatial join (geopandas + [City of Boston neighborhood boundaries GeoJSON](https://data.boston.gov/dataset/bpda-neighborhood-boundaries)).

**Before — crime.csv (district only)**

| INCIDENT_NUMBER | OFFENSE_CODE_GROUP | DISTRICT | Lat | Long |
|---|---|---|---|---|
| I182070945 | Larceny | D14 | 42.357791 | -71.139371 |
| I182070943 | Vandalism | C11 | 42.306821 | -71.060300 |
| I182070941 | Towed | D4 | 42.346589 | -71.072429 |

**After — neighborhood assigned via spatial join**

| INCIDENT_NUMBER | OFFENSE_CODE_GROUP | DISTRICT | Lat | Long | neighborhood |
|---|---|---|---|---|---|
| I182070945 | Larceny | D14 | 42.357791 | -71.139371 | Brighton |
| I182070943 | Vandalism | C11 | 42.306821 | -71.060300 | Dorchester |
| I182070941 | Towed | D4 | 42.346589 | -71.072429 | South End |

The `neighborhood` column now links crime records to any of the 15 census tables by neighborhood name. Lat/Long are preserved for mapping.
