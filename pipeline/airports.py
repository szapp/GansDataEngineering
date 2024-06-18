"""
Make API calls to RapidAPI to find the airports of cities worldwide
"""

__all__ = ["find"]

import warnings

import pandas as pd
import requests


def find(latitudes, longitudes, api_key):
    """
    Find the airports in the vicinity of the given geo coordinates

    Parameters
    ----------
    latitudes : list
        List of latitudes around which to locate airports. Must be the
        same length as longitudes

    longitudes : list
        List of longitudes around which to locate airports. Must be the
        same length as latitudes

    api_key : str
        RapidAPI key to access the Aerodatabox API

    Returns
    -------
    airports_df : pd.DataFrame
        DataFrame containing the airport information with columns
        'id', 'icao', and 'airport_name'. The column 'id' is the index
        of the location in the input list

    Raises
    ------
    ValueError
        If the length of latitudes and longitudes do not match

    Warns
    -----
    UserWarning
        If the API call fails for a location
    """
    if len(latitudes) != len(longitudes):
        raise ValueError("latitudes and longitudes must have the same length")

    url = "https://aerodatabox.p.rapidapi.com/airports/search/location"
    headers = {
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com",
        "X-RapidAPI-Key": api_key,
    }
    records = []

    for i, (lat, lon) in enumerate(zip(latitudes, longitudes)):
        params = dict(
            lat=lat,
            lon=lon,
            radiusKm="50",
            limit="5",
            withFlightInfoOnly="true",
        )
        response = requests.get(url, headers=headers, params=params)
        if not response.ok or response.status_code != 200:
            warnings.warn(f"Failed to get data for {lat}/{lon}: {response.text}")
            continue

        airport_data = pd.json_normalize(response.json()["items"])
        airport_data[["id"]] = i
        airport_data = airport_data[["id", "icao", "name"]]
        airport_data.columns = ["id", "icao", "airport_name"]
        records.append(airport_data)

    airports_df = pd.concat(records, ignore_index=True)
    return airports_df
