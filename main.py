import functions_framework
from pipeline import Database
import os


@functions_framework.http
def update_weather(request):
    """
    HTTP Cloud Function to fetch the latest weather data

    Parameters
    ----------
    request : flask.Request
        The request object

    Returns
    -------
    str
        The response text, or any set of values that can be turned into
        a Response object using `make_response`
    """
    db = Database(
        weather_api_key=os.getenv("OPENWEATHER_API_KEY"),
        rapid_api_key=os.getenv("RAPIDAPI_API_KEY"),
        database=os.getenv("MYSQL_DATABASE"),
        port=os.getenv("MYSQL_PORT"),
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        timezone="Europe/Berlin",
        reset=False,
    )
    db.fetch_weather()
    return "Success"


@functions_framework.http
def update_flights(request):
    """
    HTTP Cloud Function to fetch the latest flight data

    Parameters
    ----------
    request : flask.Request
        The request object

    Returns
    -------
    str
        The response text, or any set of values that can be turned into
        a Response object using `make_response`
    """
    db = Database(
        weather_api_key=os.getenv("OPENWEATHER_API_KEY"),
        rapid_api_key=os.getenv("RAPIDAPI_API_KEY"),
        database=os.getenv("MYSQL_DATABASE"),
        port=os.getenv("MYSQL_PORT"),
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        timezone="Europe/Berlin",
        reset=False,
    )
    db.fetch_flights()
    return "Success"
