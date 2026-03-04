import requests
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

email = os.getenv("ACLED_EMAIL")
password = os.getenv("ACLED_PASSWORD")

def get_access_token(email, password):
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

token = get_access_token(email, password)
print(f"Token obtained: {token[:20]}...")

# ── Date range ─────────────────────────────────────────────────────────────
start_date = "2025-01-01"
end_date = datetime.date.today().strftime("%Y-%m-%d")  # always today
print(f"\nFetching: {start_date} to {end_date}")

# Test 1 - try 'sort' instead of 'order'
params = {
    "iso": 804,
    "limit": 5,
    "event_date": f"{start_date}|{end_date}",
    "event_date_where": "BETWEEN",
    "_format": "json",
    "sort": "event_date",
    "direction": "desc"
}

response = requests.get(
    "https://acleddata.com/api/acled/read",
    params=params,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)

data = response.json()
print(f"Total count:  {data.get('count')}")
print(f"Dates: {[r['event_date'] for r in data.get('data', [])]}")

# ── Test 2 - remove limit to see true total count ──────────────────────────
params_no_limit = {
    "iso": 804,
    "limit": 0,                           # 0 = return all records
    "event_date": f"{start_date}|{end_date}",
    "event_date_where": "BETWEEN",
    "_format": "json",
}

response2 = requests.get(
    "https://acleddata.com/api/acled/read",
    params=params_no_limit,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
)

data2 = response2.json()
print(f"\nWith limit=0:")
print(f"Total count: {data2.get('count')}")
if data2.get('data'):
    dates = [r['event_date'] for r in data2['data']]
    print(f"Earliest date: {min(dates)}")
    print(f"Latest date:   {max(dates)}")