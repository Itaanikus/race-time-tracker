
import streamlit as st

st.set_page_config(
    page_title="Forside",
    page_icon=":material/home:"    
)

# Input new race time
st.subheader("Velkommen til KICKs race-time app.")
st.markdown(
    """ 
    Her kan du indtaste nye løbstider eller se eksisterende tider for dig og andre.

    For at indtaste en **ny tid** eller se eksisterende tider, brug menuen til venstre eller knapperne herunder.
    """
)
st.page_link("pages/1_Indtast_tid.py", label="Indtast tid", icon=":material/add:")
st.page_link("pages/2_Registrerede_tider.py", label="Registrede tider", icon=":material/table:")
st.image("assets/kick-banner.jpg")