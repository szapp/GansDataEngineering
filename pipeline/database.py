"""
This is the user interface of the pipeline. It integrates all
functions into a class to navigate the database and update it.

 - Connecting to the relational database management system
 - Creating the database with all necessary tables and relations
 - Filling the static information
 - Updating the dynamic data continuously

Examples
--------
Establish a connection

>>> from pipeline import Database
>>> db = Database(**config)

Add cities (if not already present) and their airports
>>> db.add_cities(['Berlin', 'Hamburg', 'Munich'])

Fetch dynamic data and update it in the database
>>> db.fetch_weather()
>>> db.fetch_flights()
"""

__all__ = ["Database"]

import mysql.connector
import pandas as pd

from . import airports
from . import cities
from . import flights
from . import weather


class Database:
    """
    Class to maintain and update the database
    """

    def __init__(
        self,
        weather_api_key,
        rapid_api_key,
        reset=False,
        timezone="Europe/Berlin",
        **connection
    ):
        """Initialize the database with the necessary credentials

        Parameters
        ----------
        weather_api_key : string
            API key for the weather API

        rapid_api_key : string
            API key for the rapid API

        reset : bool
            If True, the database is recreated from scratch and all data
            is lost. Default is False

        timezone : string
            Timezone to use for determining the date of the following
            day. This should be the local timezone of the base of
            operations from where the data is maintained. This setting
            is used for fetching the flight data. Default is
            'Europe/Berlin'

        connection : dict
            Connection parameters for the MySQL database

        Notes
        -----
        The connection parameters should contain the following
        keys: host, port, user, password, database. All times are in
        UTC. To relate weather and flights data to local time, use the
        timezone information in the 'geo' table.
        """
        self.weather_api_key = weather_api_key
        self.rapid_api_key = rapid_api_key
        self.timezone = timezone
        self.connection = connection
        self.connection_string = (
            "{protocol}://{user}:{password}@{host}:{port}/{database}".format(
                **connection, protocol="mysql+pymysql"
            )
        )
        self.update_parameters = dict(
            con=self.connection_string, if_exists="append", index=False
        )
        self.setup(reset)

    def setup(self, reset=False):
        """
        Setup the database and tables

        Parameters
        ----------
        reset : bool
            If True, the database is recreated from scratch and all data
            is lost
        """
        if not reset:
            # Check if database exists by attempting to connect to it
            try:
                cnx = mysql.connector.connect(**self.connection)
            except mysql.connector.Error as err:
                if err.errno != mysql.connector.errorcode.ER_BAD_DB_ERROR:
                    raise
            else:
                # It exists, so there is nothing to do here
                cnx.close()
                return

        # Connect to the MySQL server
        connection = self.connection.copy()
        db_name = connection.pop("database")
        with mysql.connector.connect(**connection) as cnx:

            # Read query from file
            with open("create_database.sql") as f:
                content = f.read()
                content = content.replace('gans_cities', db_name)
                queries = f.read().split(";")

            # Execute the queries to create the database and tables
            with cnx.cursor() as cursor:
                for query in queries:
                    cursor.execute(query)

    def add_cities(self, city_list):
        """
        Add cities to the database if they do not exist yet

        Parameters
        ----------
        city_list : list
            List of cities to add to the database

        See also
        --------
        cities.scrape : Web scraping city data
        """
        # Remove existing cities from query
        existing_cities = pd.read_sql("cities", con=self.connection_string)[
            "city_name"
        ].unique()
        city_list = list(set(city_list) - set(existing_cities))
        if len(city_list) == 0:
            return

        # Scrape the web for city data
        retrieved = cities.scrape(city_list)

        # Add the new cities to the cities table in the database
        retrieved[["city_name", "country_code"]].to_sql(
            "cities", **self.update_parameters
        )
        cities_db = pd.read_sql("cities", con=self.connection_string)

        # Merge the new population and geo data
        retr_full = cities_db.merge(retrieved)
        population = retr_full[
            ["city_id", "population", "timestamp_population"]
        ]
        geo = retr_full[["city_id", "latitude", "longitude", "timezone"]]

        # Add the new data to the database
        population.to_sql("population", **self.update_parameters)
        geo.to_sql("geo", **self.update_parameters)

        # Finally update the airports too
        self.add_airports()

    def add_airports(self):
        """
        Add airports for all cities to the database if they do not exist
        yet
        """
        # Get the cities geo data and existing airports from the
        # database
        geo_db = pd.read_sql("geo", con=self.connection_string)
        cities_id = geo_db[["city_id"]]
        airports_db = pd.read_sql("airports", con=self.connection_string)

        # Get the airports in proximity to the cities
        retrieved = airports.find(
            geo_db.latitude, geo_db.longitude, self.rapid_api_key
        )

        # Merge the airport data with the city data
        retrieved_full = cities_id.merge(
            retrieved, left_index=True, right_on="id"
        )
        retrieved_full = retrieved_full.drop(columns="id")

        # Exclude existing airports
        airports_new = retrieved_full[
            ~retrieved_full.icao.isin(airports_db.icao)
        ]

        # Add the new airports to the database
        airports_new.to_sql("airports", **self.update_parameters)

    def fetch_population(self):
        """
        Fetch the population data for the cities in the database

        Notes
        -----
        Only add rows that contain new data
        """
        # Get the cities from the database
        cities_db = pd.read_sql("cities", con=self.connection_string)

        # Scrape the web for population data
        retrieved = cities.scrape(cities_db["city_name"])
        retrieved_full = cities_db.merge(retrieved)[
            ["city_id", "population", "timestamp_population"]
        ]

        # Get the latest population data from the database to compare
        population_db = pd.read_sql("population", con=self.connection_string)
        population_db = population_db.sort_values(
            "timestamp_population"
        ).drop_duplicates(subset="city_id", keep="last")

        # Merge with latest values from the database to remove
        # duplicate rows before adding new rows to the database table
        population_new = pd.concat(
            [population_db, retrieved_full], ignore_index=True
        ).drop_duplicates(subset=retrieved_full.columns, keep=False)

        # Keep only new records and drop the population_id column
        # again
        population_new = population_new.loc[
            population_new.population_id.isna(), retrieved_full.columns
        ]

        # Add new records to the database
        population_new.to_sql("population", **self.update_parameters)

    def fetch_weather(self):
        """
        Fetch the weather data for the cities in the database
        """
        # Get the cities geo data from the database
        geo_db = pd.read_sql("geo", con=self.connection_string)
        cities_id = geo_db[["city_id"]]

        # Get the weather data
        retrieved = weather.forecast(
            geo_db.latitude, geo_db.longitude, self.weather_api_key
        )

        # Merge the weather data with the city data
        retrieved_full = cities_id.merge(
            retrieved, left_index=True, right_on="id"
        )
        retrieved_full = retrieved_full.drop(columns="id")

        # Add the weather data to the database
        retrieved_full.to_sql("weather", **self.update_parameters)

    def fetch_flights(self):
        """
        Fetch the flight data for the airports in the database
        """
        # Get the airport ICAOs from the database
        icaos = pd.read_sql("airports", con=self.connection_string)["icao"]

        # Get the flights data based on operation timezone
        retrieved = flights.fetch(icaos, self.rapid_api_key, self.timezone)

        # Add the flight data to the database
        retrieved.to_sql("flights", **self.update_parameters)
