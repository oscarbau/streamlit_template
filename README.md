 # ACLED Geospatial data viewer
 

This interactive [Streamlit](https://streamlit.io/) web app visualizes conflict event data from the [ACLED](https://acleddata.com) 
(Armed Conflict Location & Event Data Project) API, 
allowing users to select a country and time range to explore geolocated incidents such as 
battles, violence against civilians, and protests. The app uses leafmap for dynamic mapping, 
pandas for data handling, and stores fetched results in to maintain interactivity across navigation. 
Country masks are loaded as GeoJSON files to define spatial boundaries, enabling contextual 
analysis. The app is designed for humanitarian, academic, or policy users needing timely insights 
into conflict dynamics.
