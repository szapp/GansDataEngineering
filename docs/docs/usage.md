# Usage

This package can operate locally, as well as, on cloud functions. The basic usage is identical.
Specific difference are outlined in the respective sections below.

The [Database](database.md) class serves as an interface for all operations.

**Establish a connection to the database by creating a Database object.**
```python
from pipeline import Database
db = Database(**config)
```
Here, the connection details are stored in `config`, a Python dictionary with keys as outlined in the [documentation of the class](database.md).  
The SQL database will be fully **created automatically** with all its tables **if it does not exist**.
It is thus safe to re-create the Database object without data loss.

<div align="center">
  <img alt="Schema" src="../img/schema.svg">
</div>

**Add cities and their airports**
```python
db.add_cities(['Berlin', 'Hamburg', 'Munich'])
```
Only new cities will be added.
Airports in the vicinity will be added as well.

**Fetch dynamic data and update it in the database**
```python
db.fetch_weather()
db.fetch_flights()
```
These functions are to be run continuously to keep the database up-to-date.

## Local

In order to avoid hard-coding sensitive data into your Python scripts, copy the file `example.env` to your working directory with the name `.env`.
Then fill its contents with the respective credentials for a MySQL database and the necessary API keys.
Install the Python package `python-dotenv` and load the contents of the `.env` file into your environment with

```python
from dotenv import load_dotenv
load_dotenv()
```

The credentials are then securely available through the environment variables and accessible like so

```python
import os
mysql_password = os.getenv("MYSQL_PASSWORD")
```

The `Database` object from above can be created with

```python
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
```

## Google Cloud Functions

Running the pipeline on the Google Cloud Platform (GCP) requires to upload the Python package (directory `pipeline`), and the files `main.py` and `requirements.txt` to a Cloud Function.
The file `main.py` contains two possible entry points for the Cloud Function:

- `update_weather`
- `update_flights`

The functions are equipped with the `functions_framework` to allow cloud execution.

The procedure to keep the credentials secure follows as for the local usage described above.
However, the GCP offers the *Secret Manager* to store and selectively expose sensitive data.
A method that is recommended over uploading an `.env` file.

The expected names of the environment variables are the same as above, but can also be inspected or adjusted in `main.py`.
