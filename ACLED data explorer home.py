import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

# Customize the sidebar
markdown = """

# 🌍 **ACLED Conflict Viewer**

### 🛰️ *Geospatial Demo App*

---

**👤 Oscar Bautista**

*Geospatial Data Specialist*

🔗 [oscarbau.github.io](https://oscarbau.github.io)

"""

st.sidebar.title("About")
st.sidebar.info(markdown)
logo = "https://github.com/oscarbau/oscarbau.github.io/blob/main/images/compressed_favicon.png?raw=true"
st.sidebar.image(logo)

# Customize page title
st.title("""
ACLED Conflict Geospatial Data Explorer
""")

st.markdown(
    """
    This interactive [Streamlit](https://streamlit.io/) web app visualizes conflict event data from the [ACLED](https://acleddata.com) 
    (Armed Conflict Location & Event Data Project) API, 
    allowing users to select a country and time range to explore geolocated incidents such as 
    battles, violence against civilians, and protests. The app uses leafmap for dynamic mapping, 
    pandas for data handling, and stores fetched results in to maintain interactivity across navigation. 
    Country masks are loaded as GeoJSON files to define spatial boundaries, enabling contextual 
    analysis. The app is designed for humanitarian, academic, or policy users needing timely insights 
    into conflict dynamics.
    """
)

st.header("🧭 How to Use the Conflict Data Viewer")

markdown = """

Follow these steps to explore conflict events using the app:

1. ### **Navigate to the Conflict Events Page**

   * Click on **📍 ACLED conflict events** from the menu in the left panel of the app.

2. ### **Select a Country**

   * Use the dropdown menu to choose the country you’re interested in.
   * The app will automatically fetch the corresponding ISO3 code and use it to locate a geographic mask.

3. ### **Select a Date Range**

   * Choose a **start date** and an **end date** using the two calendar inputs.
   * The selected period will define the timeframe for filtering conflict events.

4. ### **Fetch Conflict Data**

   * Click the **"Fetch conflict data"** button.
   * The app will query the ACLED API using your selected country and date range.
   * If data is available, it will be stored in memory and displayed on the map.

5. ### **View the Map**

   * Once the data is fetched, a map will appear below showing conflict event locations.
   * Each event is plotted using its geographic coordinates.

6. ### **Navigate Freely**

   * If you navigate to another page and return, the map and data will still be available without needing to fetch again.

7. ### **To Refresh the Data**

   * If you want to load new data (e.g., for a different date range or country), change the inputs and click **"Fetch conflict data"** again.

---

✅ **Data Source**: [ACLED API](https://acleddata.com)

🗺️ **Technologies Used**: [Streamlit](https://streamlit.io/), 
[Leafmap](https://leafmap.org/), 
[Pandas](https://pandas.pydata.org/).

"""

st.markdown(markdown)
