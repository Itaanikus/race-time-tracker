import streamlit as st
from supabase import create_client

# Initialize the Supabase client# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_db():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)