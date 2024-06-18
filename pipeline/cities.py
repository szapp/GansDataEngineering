"""
Scrape Wikipedia for the population and other properties of cities
worldwide
"""

__all__ = [
    "scrape",
    "get_country",
    "get_country_code",
    "get_timezone",
    "get_geo",
    "get_population",
    "get_population_year",
    "get_soup",
]

from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
import warnings


def scrape(cities):
    """
    Scrape the population of selected cities worldwide from Wikipedia

    Parameters
    ----------
    cities : list
        List of city names to scrape

    Returns
    -------
    df : pd.DataFrame
        A DataFrame with the columns "city_name", "country_code",
        "population", "timestamp_population", "longitude", "latitude",
        and "timezone"

    Warns
    -----
    UserWarning
        If the scraping fails for a city
    """
    country_code_soup = get_soup("List of ISO 3166 country codes")
    timezone_soup = get_soup("List of tz database time zones")

    cities_data = []
    for city in cities:
        try:
            soup = get_soup(city)
            population = get_population(soup)
            year_population = get_population_year(soup)
            country = get_country(soup)
            country_code = get_country_code(country_code_soup, country)
            timezone = get_timezone(timezone_soup, country_code)
            latitude, longitude = get_geo(soup)
        except Exception as e:
            warnings.warn(f"Failed to scrape {city}: {e}")
            continue

        cities_data.append(
            dict(
                city_name=city,
                country_code=country_code,
                population=population,
                timestamp_population=year_population,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
            )
        )

    df = pd.DataFrame(cities_data)
    return df


def get_country(soup):
    """
    Get the country name from the Wikipedia article

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoup object for the Wikipedia article

    Returns
    -------
    country: str
        Name of the country
    """
    label = soup.find("th", class_="infobox-label", string="Country")
    country = label.find_next(class_="infobox-data").get_text(strip=True)
    country = re.match(r"^[\w\s-]+", country).group(0)
    return country


def get_country_code(soup, country):
    """
    Get the country code from the Wikipedia article

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoup object for the Wikipedia article

    country : str
        Name of the country

    Returns
    -------
    country_code : str
        ISO 3166-1 alpha-2 country code
    """
    row = soup.find("a", title=country).find_parent("td")
    country_code = row.find_next_siblings("td")[2].get_text(strip=True)
    return country_code


def get_timezone(soup, country_code):
    """
    Get the timezone from the Wikipedia article

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoup object for the Wikipedia article

    country_code : str
        ISO 3166-1 alpha-2 country code

    Returns
    -------
    tz : str
        Timezone for the country
    """
    row = soup.find(string=country_code).find_parent("td")
    tz = row.find_next_sibling("td").get_text(strip=True)
    return tz


def get_geo(soup):
    """
    Get the latitude and longitude from the Wikipedia article

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoup object for the Wikipedia article

    Returns
    -------
    latitude : float
        Latitude of the city

    longitude : float
        Longitude of the city
    """
    geo_string = soup.find("span", class_="geo").get_text()
    latitude, longitude = map(float, geo_string.split("; "))
    return latitude, longitude


def get_population(soup):
    """
    Get the population of the city from the Wikipedia article

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoup object for the Wikipedia article

    Returns
    -------
    population : int
        Population of the city
    """
    # Get the header 'Population' from the info-box table
    info_box = soup.find("table", class_="infobox")
    title_ele = info_box.find(string=re.compile(r"^[Pp]opulation")).parent

    # Differentiate between inline population and list population
    if "infobox-label" in title_ele.get("class", []):
        population_str = title_ele.find_next(class_="infobox-data").get_text()
    else:
        label_reg = re.compile(r"city|metro|municipality|total", re.I)
        data_ele = title_ele.parent.find_next_siblings(class_="mergedrow")
        row = [p for p in data_ele if label_reg.search(p.get_text())][0]
        population_str = row.find_next(class_="infobox-data").get_text()

    # Extract the population number (mind possible references [1] etc.)
    population_num = re.match(r"^[\d,]+", population_str.strip()).group(0)
    population = int(population_num.replace(",", ""))

    return population


def get_population_year(soup):
    """
    Get the year of the population data from the Wikipedia article

    Parameters
    ----------
    soup : BeautifulSoup
        BeautifulSoup object for the Wikipedia article

    Returns
    -------
    year : int
        Year of the population data
    """
    # Get the header 'Population' from the info-box table
    info_box = soup.find("table", class_="infobox")
    title_ele = info_box.find(string=re.compile(r"^[Pp]opulation")).parent

    # Extract the year from the header
    year_match = re.search(r"\d{4}", title_ele.get_text())
    year = int(year_match.group(0))

    return year


def get_soup(article):
    """
    Get the BeautifulSoup object for a given URL

    Parameters
    ----------
    article : str
        URL slug for Wikipedia article to parse

    Returns
    -------
    soup : BeautifulSoup
        BeautifulSoup object for the Wikipedia article

    Raises
    ------
    ValueError
        If the Wikipedia article is not found
    """
    article_enc = article.replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{article_enc}"
    response = requests.get(url)
    if not response.ok or response.status_code != 200:
        raise ValueError(f"Failed to reach wikipedia for '{article}'")
    soup = BeautifulSoup(response.content, "html.parser")
    return soup
