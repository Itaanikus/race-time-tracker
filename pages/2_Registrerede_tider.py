import datetime
import pandas as pd
import streamlit as st

from db_utils import init_connection
from column_names import (
    AGE,
    ID,
    NAME,
    BIRTH_DATE,
    GENDER,
    MEMBERS,
    RACETIME,
    RUNNER_ID,
    RACE_DISTANCE,
    RACE_TIME
)

st.set_page_config(
    page_title="Registrerede tider",
    page_icon=":material/table:"    
)

# region get data
supabase = init_connection()
def get_members(gender):
    if gender == "all":
        return supabase.table(MEMBERS).select(ID, NAME, BIRTH_DATE, GENDER).execute()
    return (
        supabase.table(MEMBERS)
        .select(ID, NAME, BIRTH_DATE, GENDER)
        .eq(GENDER, gender)
        .execute()
    )


def get_racetimes():
    return (
        supabase.table(RACETIME).select(RUNNER_ID, RACE_DISTANCE, RACE_TIME).execute()
    )


# endregion get data

# region create table view

def birth_date_to_age(birth_date):
    today = datetime.date.today()
    born = datetime.datetime.strptime(birth_date, "%Y-%m-%d").date()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


# Helper function to get runners and their race times
def get_runners_and_times(gender, age_range):
    # Get data
    members = get_members(gender)
    racetimes = get_racetimes()
    # create age column from birth_date
    members.data = [
        {**member, AGE: birth_date_to_age(member[BIRTH_DATE])}
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
def display_race_times_table(runner_data, distance_col):
    st.write("Race Times")
    runner_data_display = runner_data.drop(columns=[ID, RUNNER_ID, BIRTH_DATE])
    # Arrange the columns in the desired order
    runner_data_display = runner_data_display[
        [NAME, GENDER, AGE, "5", "10", "Half Marathon", "Marathon"]
    ]
    # Sort by Race Time
    runner_data_display = runner_data_display.sort_values(by=distance_col)

    st.table(runner_data_display)


# UI Setup
st.title("KICK Race Time Tracker")

# Custom CSS to change the selectbox width
st.markdown(
    """
    <style>
    .stSelectbox div {
        width: 300px;  /* Change this value to adjust the width */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Region filter by gender and age
gender_dropdown, age_dropdown = st.columns(2)
with gender_dropdown:
    gender_filter = st.selectbox(
        "Filter by Gender",
        ["all", "male", "female"],
        index=0,
        placeholder="Select gender class",
    )
with age_dropdown:
    age_filter = st.selectbox(
        "Filter by Age Group", ["all", "<20", "20-29", "30-39", "40-49", "50-59", ">59"]
    )

age_range = {
    "all": (0, 200),
    "<20": (0, 19),
    "20-29": (20, 29),
    "30-39": (30, 39),
    "40-49": (40, 49),
    "50-59": (50, 59),
    ">59": (60, 200),
}
selected_age_range = age_range.get(age_filter)


# endregion

# region sort by race times
distance_col = st.selectbox(
    "Sort by Race Time", ["5", "10", "Half Marathon", "Marathon"]
)

st.write(
    f"Filtering by {gender_filter} gender and {age_filter} age group and sorting by {distance_col} race time."
)
# Show filtered data
runner_data = get_runners_and_times(gender_filter, selected_age_range)
display_race_times_table(runner_data, distance_col)