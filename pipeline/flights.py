"""
Make API calls to RapidAPI to fetch incoming flights of cities worldwide
for the next full day
"""

__all__ = ["fetch"]

import warnings
from datetime import datetime, timedelta

import pandas as pd
import requests
from pytz import timezone as tz


def fetch(icaos, api_key, timezone="Europe/Berlin"):
    """
    Fetch the incoming flights for the airports in the list of ICAOs

    Parameters
    ----------
    icaos : list
        List of ICAO codes for the airports to fetch the incoming
        flights

    api_key : str
        RapidAPI key to access the Aerodatabox API

    timezone : str
        IANA timezone string to determine the date of the following day
        from now. This should be the local timezone of the base of
        operations from where the data is maintained. Default is
        'Europe/Berlin'

    Returns
    -------
    flight_data : pd.DataFrame
        DataFrame containing the incoming flights for the next full day
        The columns are 'flight_num', 'departure_icao', 'arrival_icao',
        'arrival_time', and 'flight_retrieved_at'

    Warns
    -----
    UserWarning
        If the API call fails for an ICAO code
    """
    url_base = "https://aerodatabox.p.rapidapi.com/flights/airports/icao"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "aerodatabox.p.rapidapi.com",
    }
    params = dict(
        withLeg="true",
        direction="Arrival",
        withCancelled="false",
        withCodeshared="true",
        withCargo="false",
        withPrivate="false",
        withLocation="false",
    )

    # Construct two time intervals to cover the full day of tomorrow
    timezone_local = tz(timezone)
    today_local = datetime.now(timezone_local).date()
    tomorrow = today_local + timedelta(days=1)
    time_slot_1 = [f"{tomorrow}T00:00", f"{tomorrow}T11:59"]
    time_slot_2 = [f"{tomorrow}T12:00", f"{tomorrow}T23:59"]

    # Define the columns to retrieve and their names
    columns = [
        "number",
        "departure.airport.icao",
        "arrival.scheduledTime.utc",
    ]
    column_names = [
        "flight_num",
        "departure_icao",
        "arrival_icao",
        "arrival_time",
        "flight_retrieved_at",
    ]

    # Iterate over ICAOs and time slots to retrieve flight data
    records = []
    for icao in icaos:
        for from_time, to_time in [time_slot_1, time_slot_2]:
            url_icao = f"{url_base}/{icao}/{from_time}/{to_time}"
            response = requests.get(url_icao, headers=headers, params=params)
            if not response.ok or response.status_code != 200:
                warnings.warn(f"Failed to fetch flights for '{icao}': {response.text}")
                continue
            data = pd.json_normalize(response.json()["arrivals"])[columns]
            data.insert(2, "icao", icao)
            data["flight_retrieved_at"] = response.headers["Date"]
            data.columns = column_names
            records.append(data)

    # Format data types
    flights = pd.concat(records, ignore_index=True)
    flights.arrival_time = pd.to_datetime(flights.arrival_time, utc=True)
    flights.flight_retrieved_at = pd.to_datetime(flights.flight_retrieved_at)
    return flights
