import streamlit as st
import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point
import os
import leafmap.foliumap as leafmap
import folium
import time


def load_acled_names():
    return pd.read_csv('https://raw.githubusercontent.com/oscarbau/streamlit_template/refs/heads/dashboards/data/acled_iso_codes.csv', delimiter=';')
     
    
acled_names= load_acled_names()

print(acled_names)