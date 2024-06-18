"""
Make API calls to OpenWeatherMap to obtain a weather forecast of cities
worldwide
"""

__all__ = ["forecast"]

import warnings

import pandas as pd
import requests


def forecast(latitudes, longitudes, api_key):
    """
    Get the weather forecast for the next 5 days for a list of cities

    Parameters
    ----------
    latitudes : list
        List of latitudes for which to get the weather forecast. Must be
        the same length as longitudes

    longitudes : list
        List of longitudes for which to get the weather forecast. Must
        be the same length as latitudes

    api_key : str
        OpenWeatherMap API key to access the weather data

    Returns
    -------
    weather : pd.DataFrame
        DataFrame containing the weather forecast for the next 5 days.
        The column 'id' is the index of the location in the input list

    Raises
    ------
    ValueError
        If the length of latitudes and longitudes do not match

    Warns
    -----
    UserWarning
        If the API call fails for a location

    Notes
    -----
    The columns are 'id', 'forecast_time', 'outlook', 'temperature',
    'feels_like', 'wind_speed', 'rain_prob', 'rain_in_last_3h', and
    'weather_retrieved_at'. All timestamps are in UTC.
    """
    if len(latitudes) != len(longitudes):
        raise ValueError("latitudes and longitudes must have the same length")

    url = "https://api.openweathermap.org/data/2.5/forecast"
    records = []

    for idx, (lat, lon) in enumerate(zip(latitudes, longitudes)):
        params = dict(lat=lat, lon=lon, appid=api_key, units="metric")
        response = requests.get(url, params)
        if not response.ok or response.status_code != 200:
            warnings.warn(f"Failed to get data for {lat:.2f}/{lon:.2f}: {response.text}")
            continue
        retrieved = response.headers["Date"]

        for w in response.json()["list"]:
            records.append(
                dict(
                    id=idx,
                    forecast_time=w.get("dt"),
                    outlook=w["weather"][0].get("description"),
                    temperature=w["main"].get("temp"),
                    feels_like=w["main"].get("feels_like"),
                    wind_speed=w["wind"].get("speed"),
                    rain_prob=w.get("pop", 0),
                    rain_in_last_3h=w.get("rain", dict()).get("3h", 0),
                    weather_retrieved_at=retrieved,
                )
            )

    # Convert to DataFrame and adjust datatypes
    weather = pd.DataFrame(records)
    weather.forecast_time = pd.to_datetime(weather.forecast_time, unit="s")
    weather.weather_retrieved_at = pd.to_datetime(weather.weather_retrieved_at)
    return weather
