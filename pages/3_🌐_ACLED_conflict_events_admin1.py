import streamlit as st
import geopandas as gpd
import requests
import leafmap.foliumap as leafmap
import pandas as pd

st.title("Conflict Explorer subnational level")

def get_boundaries_ADM1(iso3):
    # Get the metadata from the GeoBoundaries API
    url = f"https://www.geoboundaries.org/api/current/gbOpen/{iso3}/ADM1/"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Could not fetch data for {iso3}, status code: {response.status_code}")

    metadata = response.json()
    
    # Extract the simplified GeoJSON URL
    simplified_url = metadata.get("simplifiedGeometryGeoJSON")
    if not simplified_url:
        raise ValueError("No simplifiedGeometryGeoJSON found in API response.")

    # Read the GeoJSON into a GeoDataFrame
    boundary_polygons = gpd.read_file(simplified_url)
    return boundary_polygons



if "geo_acled" in st.session_state:
    geo_acled = st.session_state["geo_acled"]
    center_latlon = st.session_state["center_latlon"]
    selected_country = st.session_state["selected_country"]
    selected_iso3 = st.session_state["selected_iso3"]
    st.success(f"Adm1 data loaded for {selected_country}")

    with st.expander("See DataFrame"):
            st.dataframe(geo_acled)
    
    geo_acled['event_date'] = pd.to_datetime(geo_acled['event_date'], format="%Y-%m-%d", errors='coerce')


    geo_acled['month_date'] = geo_acled['event_date'].dt.to_period('M').dt.to_timestamp()

    

    # Group by month and admin1
    monthly_fatalities = geo_acled.groupby(['month_date', 'admin1'])['fatalities'].sum().reset_index()

    # Pivot the table so each admin1 is a column
    pivot_df = monthly_fatalities.pivot(index='month_date', columns='admin1', values='fatalities')
    pivot_df = pivot_df.fillna(0)  # Fill NaNs with 0
    # print(geo_acled["event_date"].min())
    # print(geo_acled["event_date"].max())



    boundary_polygons = get_boundaries_ADM1(selected_iso3)

    # Perform a spatial join to associate points with polygons
    spatial_join = gpd.sjoin(geo_acled, boundary_polygons, how='inner', predicate='intersects')
    # Group by the 'ADM1' and calculate the sum of fatalities
    aggregated_data = spatial_join.groupby('shapeName')['fatalities'].sum().reset_index()
    # print(aggregated_data.head())
    # Merge the aggregated data back into the boundary polygon dataset
    fatalities_adm1 = boundary_polygons.merge(aggregated_data, on='shapeName', how='left')
    fatalities_adm1['fatalities']=fatalities_adm1['fatalities'].fillna(0)
    max_fat = fatalities_adm1['fatalities'].max()

    m = leafmap.Map(center=center_latlon, zoom=4)

    m.add_data(fatalities_adm1,
                column="fatalities",
                scheme="NaturalBreaks", 
                cmap="Reds", 
                legend_title="Fatalities by Adm1",
                layer_name = "Fatalities by Adm1"
            )

    col1, col2 = st.columns(2)

    with col1:
        m.to_streamlit(height=300, width=400)
    
    
    with col2:
        st.bar_chart(pivot_df)
        
else:
    st.warning("No conflict data loaded. Please go to the conflict events data page first.")