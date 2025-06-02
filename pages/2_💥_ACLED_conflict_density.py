import streamlit as st
import leafmap.foliumap as leafmap

st.title("Conflict density Explorer")

if "geo_acled" in st.session_state and "center_latlon":
    geo_acled = st.session_state["geo_acled"]
    center_latlon = st.session_state["center_latlon"]
    st.success(f"Loaded {len(geo_acled)} conflict events from session.")

    m = leafmap.Map(center= center_latlon, zoom=4)
    m.add_heatmap(
        geo_acled,
        latitude="latitude",
        longitude="longitude",
        value="fatalities",
        name="Conflict Heatmap",
        radius=20,
    )
    m.to_streamlit(height=500)
else:
    st.warning("No conflict data loaded. Please go to the conflict events data page first.")


