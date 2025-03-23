import datetime
import streamlit as st

from utils.db_utils import init_db
from utils.date_utils import convert_date_to_age
from column_names import (
    ID,
    NAME,
    AGE,
    BIRTH_DATE,
    GENDER,
    MEMBERS,
    RACE_LOCATION,
    RACETIME,
    RUNNER_ID,
    RACE_DISTANCE,
    RACE_TIME,
    RACE_DATE,
)


st.subheader("Indtast en ny løbstid")

# Inputs with session state defaults
if "name" not in st.session_state:
    st.session_state["name"] = ""
name_input = st.text_input("Navn", value=st.session_state["name"], placeholder="Morten Westergaard")

if "birth_date" not in st.session_state:
    st.session_state["birth_date"] = datetime.date(2000, 1, 1)
birth_date_input = st.date_input("Fødselsdag", value=st.session_state["birth_date"])

if "gender" not in st.session_state:
    st.session_state["gender"] = "Mand"
gender_input = st.selectbox("Køn", ["Mand", "Kvinde"], index=["Mand", "Kvinde"].index(st.session_state["gender"]))

distance_input = st.selectbox(
    "Løbsdistance", ["5K", "10K", "Half Marathon", "Marathon"]
)
time_input = st.text_input("Indtast race-tid (HH:MM:SS)", placeholder="00:00:00")
race_date_input = st.date_input("Dato for løb")
race_location_input = st.text_input("Angiv navn på løbet", placeholder="Royal Run")

if st.button("Indsend tid"):
    # Parse race time
    try:
        race_time = datetime.datetime.strptime(time_input, "%H:%M:%S").time()
    except ValueError:
        st.error("Forkert tidsformat. Indtast venligst tid i HH:MM:SS format.")
        race_time = None

    if race_time:
        supabase = init_db()

        existing_runner = (
            supabase.table(MEMBERS).select(ID).eq(NAME, name_input).execute()
        )

        if existing_runner.data:
            runner_id = existing_runner.data[0][ID]
        else:
            parsed_birth_date = str(birth_date_input)
            runner_data = {
                NAME: name_input,
                BIRTH_DATE: parsed_birth_date,
                GENDER: gender_input,
            }
            new_runner = supabase.table(MEMBERS).insert(runner_data).execute()
            runner_id = new_runner.data[0]["id"]

        # Insert or update the race time
        race_data = {
            RUNNER_ID: runner_id,
            RACE_DISTANCE: distance_input,
            RACE_TIME: time_input,
            RACE_DATE: str(race_date_input),
            RACE_LOCATION: race_location_input,
        }

        supabase.table(RACETIME).insert(race_data).execute()

        st.session_state["name"] = name_input
        st.session_state["birth_date"] = birth_date_input
        st.session_state["gender"] = gender_input
        st.success(f"Race time for {name_input} added successfully!")
