import datetime
import pandas as pd
import streamlit as st
from supabase import create_client

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
    RACE_TIME,
)


# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    # url = st.secrets["SUPABASE_URL"]
    # key = st.secrets["SUPABASE_KEY"]
    url = "https://pryzvkhecuievhfgyjfu.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByeXp2a2hlY3VpZXZoZmd5amZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzkxMDExMzAsImV4cCI6MjA1NDY3NzEzMH0.W15HIDZ3p2mCcTBGKiIrnu4kEiKLac4r9H5NYnxl8Vw"
    return create_client(url, key)


# Initialize the Supabase client
supabase = init_connection()


# region get data
# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
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

st.write(f"Filtering by {gender_filter} gender and {age_filter} age group.")
# Show filtered data
runner_data = get_runners_and_times(gender_filter, selected_age_range)
display_race_times_table(runner_data, distance_col)

# Input new race time
st.header("Input New Race Time")

name_input = st.text_input("Enter Runner Name")
birth_date_input = st.date_input("Enter Birth Date", value=datetime.date(2000, 1, 1))
gender_input = st.selectbox("Select Gender", ["male", "female"])

distance_input = st.selectbox("Race Distance", ["5", "10", "Half Marathon", "Marathon"])
time_input = st.text_input("Enter Race Time (HH:MM:SS)", placeholder="00:00:00")

if st.button("Submit New Race Time"):
    # Parse race time
    try:
        race_time = datetime.datetime.strptime(time_input, "%H:%M:%S").time()
    except ValueError:
        st.error("Invalid time format. Please use HH:MM:SS format.")
        race_time = None

    if race_time:
        # Check if the name exists, otherwise create a new entry
        existing_runner = (
            supabase.table(MEMBERS).select(ID).eq(NAME, name_input).execute()
        )
        if existing_runner.data:
            runner_id = existing_runner.data[0][ID]
        else:
            runner_data = {
                NAME: name_input,
                BIRTH_DATE: str(birth_date_input),
                GENDER: gender_input,
            }
            new_runner = supabase.table(MEMBERS).insert(runner_data).execute()
            runner_id = new_runner.data[0]["id"]

        # Insert or update the race time
        race_data = {
            RUNNER_ID: runner_id,
            RACE_DISTANCE: distance_input,
            RACE_TIME: time_input,
        }
        supabase.table(RACETIME).insert(race_data).execute()

        st.success(f"Race time for {name_input} added successfully!")
