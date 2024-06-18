/***************************
Setting up the environment
***************************/

/* The database name 'gans_cities' will be replaced */

-- Drop the database if it already exists
DROP DATABASE IF EXISTS gans_cities;

-- Create the database
CREATE DATABASE gans_cities;

-- Use the database
USE gans_cities;


/*******************
Creating the tables
********************/

-- Static information about cities
CREATE TABLE cities (
    city_id INT AUTO_INCREMENT,
    city_name VARCHAR(255),
    country_code VARCHAR(10),
    PRIMARY KEY (city_id)
);

-- Static information about geographical locations
CREATE TABLE geo (
    city_id INT,
	latitude FLOAT,
    longitude FLOAT,
    timezone VARCHAR(255),
    PRIMARY KEY (city_id),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);

-- Static information about airports
CREATE TABLE airports (
    icao VARCHAR(10),
    city_id INT NOT NULL,
    airport_name VARCHAR(255),
    PRIMARY KEY (icao),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);

-- Semi-static information about city populations
CREATE TABLE population (
    population_id INT AUTO_INCREMENT,
    city_id INT NOT NULL,
    population INT,
    timestamp_population YEAR,
    PRIMARY KEY (population_id),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);

-- Dynamic information about weather
CREATE TABLE weather (
    weather_id INT AUTO_INCREMENT,
    city_id INT NOT NULL,
    outlook VARCHAR(255),
	forecast_time DATETIME,
    temperature FLOAT,
    feels_like FLOAT,
    wind_speed FLOAT,
    rain_prob FLOAT,
    rain_in_last_3h FLOAT,
    weather_retrieved_at DATETIME,
    PRIMARY KEY (weather_id),
    FOREIGN KEY (city_id) REFERENCES cities(city_id)
);

-- Dynamic information about incoming flights
CREATE TABLE flights (
    flight_id INT AUTO_INCREMENT,
    flight_num VARCHAR(25),
    departure_icao VARCHAR(25),
    arrival_icao VARCHAR(25),
    arrival_time DATETIME,
    flight_retrieved_at DATETIME,
    PRIMARY KEY (flight_id),
    FOREIGN KEY (arrival_icao) REFERENCES airports(icao)
)
