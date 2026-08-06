import datetime
import requests
import json
import math

def get_annual_gdd(lat=39.5146, lon=3.2124) -> float:
    try:
        now = datetime.datetime.now()
        year = now.year
        start_date = f"{year}-03-01"
        end_date = now.strftime("%Y-%m-%d")
        
        if now.month < 3:
            return 0.0

        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_mean",
            "timezone": "Europe/Madrid"
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        if "daily" not in data or "temperature_2m_mean" not in data["daily"]:
            return -1.0
            
        tmeans = data["daily"]["temperature_2m_mean"]
        total_gdd = 0.0
        for t in tmeans:
            if t is not None:
                total_gdd += max(t - 10.0, 0.0)
                
        return round(total_gdd, 1)
    except Exception as e:
        print(f"Error fetching annual GDD: {e}")
        return -1.0

if __name__ == "__main__":
    print(f"GDD Anual des de l'1 de març: {get_annual_gdd()}")
