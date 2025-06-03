import streamlit as st

st.title("Conflict Explorer subnational level")


if "geo_acled" in st.session_state and "center_latlon":
    geo_acled = st.session_state["geo_acled"]
    center_latlon = st.session_state["center_latlon"]
    selected_country = st.session_state["selected_country"] 
    st.header(f"{selected_country} ADM1")
else:
    st.warning("No conflict data loaded. Please go to the conflict events data page first.")