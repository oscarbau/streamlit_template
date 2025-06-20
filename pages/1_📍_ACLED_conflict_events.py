import streamlit as st
import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point
import os
import leafmap.foliumap as leafmap
import folium
import time

st.title("Conflict Data Explorer")

@st.cache_data
def load_country_dict():
    world = pd.read_json('https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/refs/heads/master/all/all.json')
    country_dict = {
        row['name']: {
            'alpha3': row['alpha-3'],
            'country_code': row['country-code']
        }
        for _, row in world.iterrows()
    }
    return country_dict

@st.cache_data
def load_acled_names():
    return pd.read_csv('https://raw.githubusercontent.com/oscarbau/streamlit_template/refs/heads/dashboards/data/acled_iso_codes.csv', delimiter=';')
    
acled_names= load_acled_names()

# Create mapping from numeric ISO code → ACLED country name
code_to_acled_name = dict(zip(acled_names['ISO Codes'], acled_names['Country']))


country_dict = load_country_dict()

# Add 'acled_name' to each entry in the dictionary
for name, data in country_dict.items():
    code = data.get("country_code")
    acled_name = code_to_acled_name.get(code)
    data["acled_name"] = acled_name if acled_name else None

@st.cache_data
def get_conflict(period, iso, iso3):
    # Attempt to load local .env file, if available (only applies locally)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # dotenv not installed or not needed on cloud
        pass

    # Now load environment variables
    api_key = os.getenv("ACLED_API_KEY")
    email = os.getenv("ACLED_EMAIL")

    if not api_key or not email:
        raise ValueError("Missing ACLED_API_KEY or ACLED_EMAIL environment variables.")
    
    start_date_str, end_date_str = period.split('/')
    start_date = pd.to_datetime(start_date_str).strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date_str).strftime("%Y-%m-%d")

    all_data = []

    current_start = start_date
    # while current_start <= end_date:
    #     current_end = min(current_start.replace(month=12, day=31), end_date)

    url = (
        f'https://api.acleddata.com/acled/read?'
        f'key={api_key}&email={email}&'
        f'iso={iso}&limit=0&'
        f'event_date={start_date}|{end_date}&'
        f'event_date_where=BETWEEN'
    )

    # print(url)
    
    response = requests.get(url)
    if response.status_code != 200:
        st.error(f'ACLED API request failed with status code: {response.status_code}')
        return None

    data = response.json()
    if 'data' not in data:
        st.error("No 'data' key in ACLED API response.")
        return None
    
    if data.get("success") is True and data.get("count", 0) == 0:
        st.markdown(" ")
        st.markdown(" ")
        st.warning("No data available for this period, please select a more recent period.")
        st.cache_data.clear()  # Clears all @st.cache_data
        st.cache_resource.clear()
        time.sleep(5)
        st.rerun()
        return None

    for record in data['data']:
        event_date = record.get('event_date', '')
        year, month, day = (event_date.split('-') + [None, None, None])[:3]
        formatted_record = {
            'event_id_cnty': record.get('event_id_cnty'),
            'event_date': event_date,
            'year': int(year) if year else None,
            'month': int(month) if month else None,
            'day': int(day) if day else None,
            'actor1': record.get('actor1'),
            'actor2': record.get('actor2'),
            'interaction': record.get('interaction'),
            'country': record.get('country'),
            'admin1': record.get('admin1'),
            'admin2': record.get('admin2'),
            'admin3': record.get('admin3'),
            'location': record.get('location'),
            'fatalities': int(record.get('fatalities', 0)),
            'latitude': float(record.get('latitude', 0)),
            'longitude': float(record.get('longitude', 0)),
            'geo_precision': record.get('geo_precision')
        }
        all_data.append(formatted_record)

    num_records = len(data['data'])
    print(f"{num_records} events feteched for the period {start_date} to {end_date}")        
    # current_start = current_end + pd.Timedelta(days=1)
        

    df = pd.DataFrame(all_data)
    
    df['event_date'] = pd.to_datetime(df['event_date'], format="%Y-%m-%d", errors='coerce')
    # df_period = df[df['event_date'].between(start_date, end_date)].copy()

    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    mask_gdf = get_mask_for_iso3(iso3)
    mask_gdf = mask_gdf.to_crs(gdf.crs)

    centroid = mask_gdf.geometry.unary_union.centroid
    center_latlon = [centroid.y, centroid.x]
    
    # Clip points to mask
    # geo_acled = gpd.clip(gdf, mask_gdf)
    geo_acled = gdf
    if geo_acled.empty:
        st.warning("No conflict events found within the selected mask and period.")
        return None

    geo_acled['event_date'] = geo_acled['event_date'].dt.strftime('%Y-%m-%d')

    return geo_acled, center_latlon, df

@st.cache_data
def get_mask_for_iso3(iso3):
        url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
        countries = gpd.read_file(url)
        country_mask = countries[countries['ISO3166-1-Alpha-3'] == iso3]
        if country_mask.empty:
            raise ValueError(f"No country found with ISO3 code {iso3}")
        return country_mask


 # Load country dictionary
country_dict = load_country_dict()

# Streamlit widgets

col1, col2, col3 = st.columns(3)
with col1:
    current_selection = st.selectbox(
    "Select a country",
    sorted(country_dict.keys()),
    index=sorted(country_dict.keys()).index(
        st.session_state.get("selected_country", sorted(country_dict.keys())[0])
    )
)
    
# Detect change and clear session state (except current selection)
if (
    "selected_country" in st.session_state
    and current_selection != st.session_state.selected_country
):
    selected_value = current_selection  # temporarily store new value
    st.session_state.clear()  # clear all previous outputs/maps
    st.session_state.selected_country = selected_value  # restore current selection
    st.rerun()  # rerun the app with a clean state

# Store current selection
st.session_state.selected_country = current_selection
selected_country = current_selection

selected_country_name = country_dict[selected_country]
selected_iso3 = selected_country_name['alpha3']
selected_iso_num = selected_country_name['country_code']

# st.write(f"Selected country: **{selected_country}**")
# st.write(f"ISO3 code: **{selected_iso3}**")
# st.write(f"ISO numeric code: **{selected_iso_num}**")

# Separate date inputs for start and end date
with col2:
    start_date = st.date_input(
        "Select start date",
        value=st.session_state.get("start_date", pd.to_datetime("2025-01-01")),
        min_value="2000-01-01",
        max_value=pd.Timestamp.today()
    )
with col3:
    end_date = st.date_input(
        "Select end date",
        value=st.session_state.get("end_date", pd.Timestamp.today()),
        min_value=start_date,  # Prevent end date before start date
        max_value=pd.Timestamp.today()
    )

# Convert dates to string format for API (YYYY-MM-DD/YYYY-MM-DD)
period = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

# Build mask path automatically from iso3 (adjust folder structure as needed)
mask_path = f"masks/{selected_iso3}.geojson"

fetch_data = st.button("Fetch conflict data")
def main():
    if fetch_data:
        
        geojson, center_latlon, df = get_conflict(period, selected_iso_num, selected_iso3)
        with st.expander("See DataFrame"):
            st.dataframe(df)
        date_first = geojson["event_date"].min()
        date_last = geojson["event_date"].max()
        st.success(f"Fetched {len(geojson)} conflict events from {date_first} to {date_last} for {selected_country}.")
        
    
        if geojson is None:
            st.error("No confict data found.")
            st.stop()

        # Save to session state, including current inputs to keep state in sync
        st.session_state["selected_country"] = selected_country
        st.session_state["start_date"] = start_date
        st.session_state["end_date"] = end_date
        st.session_state["geo_acled"] = geojson
        st.session_state["center_latlon"] = center_latlon
        st.session_state["selected_iso3"] = selected_iso3
        st.session_state["data_loaded"] = True


    # This is true just after clicking the button
    if st.session_state.get("data_loaded"):
        geo_acled = st.session_state["geo_acled"]
        center_latlon = st.session_state["center_latlon"]

        def get_color(value):
            return "red" if value > 0 else "black"
        
        m = leafmap.Map(center=center_latlon, zoom=4)
        labels = ["fatal event", "non fatal event"]
        colors = ["#FF0000", "#000000"]
        for _, row in geo_acled.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                color=get_color(row['fatalities']),
                fill=True,
                fill_color=get_color(row['fatalities']),
                fill_opacity=0.7,
                popup=f"Fatalities: {row['fatalities']}\nAdmin1: {row['admin1']}\nEvent date: {row['event_date']}"
                ).add_to(m)
        m.add_legend(title="Legend", labels=labels, colors=colors)
        m.to_streamlit(height=500)

if __name__ == "__main__":
    main()
    