import streamlit as st
import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point
import os
import leafmap.foliumap as leafmap
import folium
import datetime
from dotenv import load_dotenv

# ── Environment ────────────────────────────────────────────────────────────
load_dotenv()
email = os.getenv("ACLED_EMAIL")
password = os.getenv("ACLED_PASSWORD")

if not email or not password:
    st.error("Missing ACLED_EMAIL or ACLED_PASSWORD. Please set them in your environment or Space secrets.")
    st.stop()

# ── Page config ────────────────────────────────────────────────────────────
st.title("Conflict Data Explorer")

# ── Cached helpers ─────────────────────────────────────────────────────────
@st.cache_data
def load_country_dict():
    world = pd.read_json(
        'https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes'
        '/refs/heads/master/all/all.json'
    )
    return {
        row['name']: {
            'alpha3': row['alpha-3'],
            'country_code': row['country-code']
        }
        for _, row in world.iterrows()
    }

@st.cache_data
def load_acled_names():
    return pd.read_csv(
        'https://raw.githubusercontent.com/oscarbau/streamlit_template'
        '/refs/heads/dashboards/data/acled_iso_codes.csv',
        delimiter=';'
    )

@st.cache_data(ttl=3600)  # refresh token every hour
def get_access_token(email, password):
    """Get OAuth2 Bearer token from ACLED."""
    response = requests.post(
        "https://acleddata.com/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "username": email,
            "password": password,
            "grant_type": "password",
            "client_id": "acled"
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get token: {response.status_code} {response.text}")

@st.cache_data
def get_mask_for_iso3(iso3):
    url = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
    countries = gpd.read_file(url)
    country_mask = countries[countries['ISO3166-1-Alpha-3'] == iso3]
    if country_mask.empty:
        raise ValueError(f"No country found with ISO3 code: {iso3}")
    return country_mask

@st.cache_data(ttl=1800)  # refresh data every 30 min
def fetch_conflict_data(period, iso, iso3):
    """Pure data fetching — no st.* calls so caching works safely."""
    start_date_str, end_date_str = period.split('/')
    start_date = pd.to_datetime(start_date_str).strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date_str).strftime("%Y-%m-%d")

    token = get_access_token(email, password)

    params = {
        "iso": iso,
        "limit": 0,
        "event_date": f"{start_date}|{end_date}",
        "event_date_where": "BETWEEN",
        "_format": "json"
    }

    response = requests.get(
        "https://acleddata.com/api/acled/read",
        params=params,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )

    if response.status_code != 200:
        raise Exception(f"ACLED API request failed: {response.status_code}")

    data = response.json()

    if 'data' not in data:
        raise Exception("No 'data' key in ACLED API response.")

    if data.get("count", 0) == 0:
        return None  # caller handles empty result

    all_data = []
    for record in data['data']:
        event_date = record.get('event_date', '')
        year, month, day = (event_date.split('-') + [None, None, None])[:3]
        all_data.append({
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
        })

    print(f"{len(all_data)} events fetched for {start_date} to {end_date}")

    df = pd.DataFrame(all_data)
    df['event_date'] = pd.to_datetime(df['event_date'], format="%Y-%m-%d", errors='coerce')

    geometry = [Point(xy) for xy in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    mask_gdf = get_mask_for_iso3(iso3).to_crs(gdf.crs)
    centroid = mask_gdf.geometry.unary_union.centroid
    center_latlon = [centroid.y, centroid.x]

    if gdf.empty:
        return None

    gdf['event_date'] = gdf['event_date'].dt.strftime('%Y-%m-%d')

    return gdf, center_latlon, df


# ── Load reference data ────────────────────────────────────────────────────
country_dict = load_country_dict()
acled_names = load_acled_names()
code_to_acled_name = dict(zip(acled_names['ISO Codes'], acled_names['Country']))

for name, data in country_dict.items():
    code = data.get("country_code")
    data["acled_name"] = code_to_acled_name.get(code)


# ── UI ─────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

with col1:
    current_selection = st.selectbox(
        "Select a country",
        sorted(country_dict.keys()),
        index=sorted(country_dict.keys()).index(
            st.session_state.get("selected_country", sorted(country_dict.keys())[0])
        )
    )

# Clear state if country changed
if (
    "selected_country" in st.session_state
    and current_selection != st.session_state.selected_country
):
    keys_to_keep = {"selected_country"}
    for key in list(st.session_state.keys()):
        if key not in keys_to_keep:
            del st.session_state[key]
    st.session_state.selected_country = current_selection
    st.rerun()

st.session_state.selected_country = current_selection
selected_country = current_selection
selected_iso3 = country_dict[selected_country]['alpha3']
selected_iso_num = country_dict[selected_country]['country_code']

with col2:
    start_date = st.date_input(
        "Select start date",
        value=st.session_state.get("start_date", datetime.date(2025, 1, 1)),
        min_value=datetime.date(2000, 1, 1),
        max_value=datetime.date.today()
    )
with col3:
    end_date = st.date_input(
        "Select end date",
        value=st.session_state.get("end_date", datetime.date.today()),
        min_value=start_date,
        max_value=datetime.date.today()
    )

period = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    fetch_data = st.button("Fetch conflict data")

    if fetch_data:
        with st.spinner("Fetching conflict data..."):
            try:
                result = fetch_conflict_data(period, selected_iso_num, selected_iso3)
            except Exception as e:
                st.error(f"Failed to fetch data: {e}")
                return

        if result is None:
            st.warning("No data available for this period. Please select a more recent date range.")
            return

        geojson, center_latlon, df = result

        # Save to session state for other pages
        st.session_state["selected_country"] = selected_country
        st.session_state["start_date"] = start_date
        st.session_state["end_date"] = end_date
        st.session_state["geo_acled"] = geojson
        st.session_state["center_latlon"] = center_latlon
        st.session_state["selected_iso3"] = selected_iso3
        st.session_state["df"] = df
        st.session_state["data_loaded"] = True

        st.success(
            f"Fetched {len(geojson)} conflict events from "
            f"{geojson['event_date'].min()} to {geojson['event_date'].max()} "
            f"for {selected_country}."
        )
        with st.expander("See DataFrame"):
            st.dataframe(df)

    # Render map if data is available
    if st.session_state.get("data_loaded"):
        geo_acled = st.session_state["geo_acled"]
        center_latlon = st.session_state["center_latlon"]

        def get_color(value):
            return "red" if value > 0 else "black"

        m = leafmap.Map(center=center_latlon, zoom=4)
        for _, row in geo_acled.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=6,
                color=get_color(row['fatalities']),
                fill=True,
                fill_color=get_color(row['fatalities']),
                fill_opacity=0.7,
                popup=(
                    f"Fatalities: {row['fatalities']}\n"
                    f"Admin1: {row['admin1']}\n"
                    f"Event date: {row['event_date']}"
                )
            ).add_to(m)
        m.add_legend(
            title="Legend",
            labels=["Fatal event", "Non-fatal event"],
            colors=["#FF0000", "#000000"]
        )
        m.to_streamlit(height=500)


if __name__ == "__main__":
    main()