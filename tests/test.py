import requests
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("ACLED_API_KEY")
email = os.getenv("ACLED_EMAIL")

url = "https://acleddata.com/api/acled/read"
params = {
    "key": api_key,
    "email": email,
    "iso": 4,
    "limit": 1,  # just fetch 1 row to test
}

response = requests.get(url, params=params)
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")