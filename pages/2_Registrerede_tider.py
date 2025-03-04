import pandas as pd
import streamlit as st

from st_aggrid import AgGrid, ColumnsAutoSizeMode
from utils.db_utils import init_db
from utils.date_utils import convert_date_to_age
from column_names import (
    AGE,
    AGE_HEADER,
    GENDER_HEADER,
    ID,
    NAME,
    BIRTH_DATE,
    GENDER,
    MEMBERS,
    NAME_HEADER,
    RACETIME,
    RUNNER_ID,
    RACE_DISTANCE,
    RACE_TIME,
    RACE_LOCATION,
)

st.set_page_config(page_title="Registrerede tider", page_icon=":material/table:")

# region get data
supabase = init_db()


def get_members(gender):
    if gender == "Alle":
        return supabase.table(MEMBERS).select(ID, NAME, BIRTH_DATE, GENDER).execute()
    return (
        supabase.table(MEMBERS)
        .select(ID, NAME, BIRTH_DATE, GENDER)
        .eq(GENDER, gender)
        .execute()
    )


def get_racetimes():
    return (
        supabase.table(RACETIME)
        .select(RUNNER_ID, RACE_DISTANCE, RACE_TIME, RACE_LOCATION)
        .execute()
    )


# endregion get data

# region create table view


# Helper function to get runners and their race times
def get_runners_and_times(gender, age_range):
    # Get data
    members = get_members(gender)

    if not members or not members.data:
        return None

    racetimes = get_racetimes()

    # create age column from birth_date
    members.data = [
        {**member, AGE: convert_date_to_age(member[BIRTH_DATE])}
        for member in members.data
    ]

    members_df = pd.DataFrame(members.data)

    # filter by age range
    if age_range:
        members_df = members_df[
            (members_df[AGE] >= age_range[0]) & (members_df[AGE] <= age_range[1])
        ]

    racetimes_df = pd.DataFrame(racetimes.data)

    # only take fastest time for each distance
    racetimes_df = racetimes_df.loc[
        racetimes_df.groupby([RUNNER_ID, RACE_DISTANCE])[RACE_TIME]
        .transform("min")
        .eq(racetimes_df[RACE_TIME])
    ].reset_index(drop=True)

    # from racetimes_df create new columns named the distance and the time as the value
    racetimes_df = racetimes_df.pivot(
        index=RUNNER_ID, columns=RACE_DISTANCE, values=RACE_TIME
    ).reset_index()

    # Merge the two dataframes
    merged_df = pd.merge(
        members_df, racetimes_df, left_on=ID, right_on=RUNNER_ID, how="left"
    )

    return merged_df


# Function to display the race times table
def display_race_times_table(runner_data):
    runner_data_display = runner_data.drop(columns=[ID, RUNNER_ID, BIRTH_DATE])
    columns = [NAME, GENDER, AGE, "5K", "10K", "Half Marathon", "Marathon"]

    for col in columns:
        if col not in runner_data_display.columns:
            runner_data_display[col] = pd.NA  # Assign NaN to missing columns

    runner_data_display = runner_data_display[
        [NAME, GENDER, AGE, "5K", "10K", "Half Marathon", "Marathon"]
    ]

    # Sort by Race Time
    return runner_data_display


# UI Setup
st.title("KICK Race Time Tracker")

# Region filter by gender and age
gender_dropdown, age_dropdown = st.columns(2)
with gender_dropdown:
    gender_filter = st.selectbox(
        "Filtrer på køn",
        ["Alle", "Mand", "Kvinde"],
        index=0,
        placeholder="Vælg køn",
    )
with age_dropdown:
    age_filter = st.selectbox(
        "Filtrer på aldersgruppe",
        ["Alle", "<20", "20-29", "30-39", "40-49", "50-59", ">59"],
    )

age_range = {
    "Alle": (0, 200),
    "<20": (0, 19),
    "20-29": (20, 29),
    "30-39": (30, 39),
    "40-49": (40, 49),
    "50-59": (50, 59),
    ">59": (60, 200),
}
selected_age_range = age_range.get(age_filter)


# endregion

st.text(
    f"""
    Viser oversigt med følgende filtre:
    Køn: {gender_filter}
    Aldersgruppe: {age_filter}
    """
)
# Show filtered data
runner_data = get_runners_and_times(gender_filter, selected_age_range)

grid_options = {
    "columnDefs": [
        {"headerName": NAME_HEADER, "field": NAME},
        {"headerName": GENDER_HEADER, "field": GENDER},
        {"headerName": AGE_HEADER, "field": AGE},
        {"headerName": "5K", "field": "5K"},
        {"headerName": "10K", "field": "10K"},
        {"headerName": "Half Marathon", "field": "Half Marathon"},
        {"headerName": "Marathon", "field": "Marathon"},
    ],
}

st.write("Race Times")
if runner_data is None:
    AgGrid(pd.DataFrame(grid_options), gridOptions=grid_options)
else:
    AgGrid(
        display_race_times_table(runner_data),
        gridOptions=grid_options,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
    )
