#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module to scrape 5-min personal weather station data from Weather Underground.

Usage is:
>>> python scrape_wunderground.py   STATION    DATE     FREQ

where station is a personal weather station (e.g., KCAJAMES3), date is in the
format YYYY-MM-DD and FREQ is either 'daily' or '5min' (for daily or 5-minute
observations, respectively).

Alternatively, each function below can be imported and used in a separate python
script. Note that a working version of chromedriver must be installed and the absolute
path to executable has to be updated below ("chromedriver_path").

Zach Perzan, 2021-07-28"""

import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as BS
from selenium import webdriver
import argparse

# Set the absolute path to chromedriver
chromedriver_path = '/bin/chromedriver'


def render_page(url):
    """Given a url, render it with chromedriver and return the html source

    Parameters
    ----------
        url : str
            url to render

    Returns
    -------
        r :
            rendered page source
    """

    driver = webdriver.Chrome(chromedriver_path)
    driver.get(url)
    time.sleep(3) # Could potentially decrease the sleep time
    r = driver.page_source
    driver.quit()

    return r


def scrape_wunderground(station, date, freq='5min'):
    """Given a PWS station ID and date, scrape that day's data from Weather
    Underground and return it as a dataframe.

    Parameters
    ----------
        station : str
            The personal weather station ID
        date : str
            The date for which to acquire data, formatted as 'YYYY-MM-DD'
        freq : {'5min', 'daily'}
            Whether to download 5-minute weather observations or daily
            summaries (average, min and max for each day)

    Returns
    -------
        df : dataframe or None
            A dataframe of weather observations, with index as pd.DateTimeIndex
            and columns as the observed data
    """

    # the url for 5-min data is called "daily" on weather underground
    if freq == '5min':
        timespan = 'daily'
    # the url for daily summary data (avg/min/max) is called "monthly" on wunderground
    elif freq == 'daily':
        timespan = 'monthly'

    # Render the url and open the page source as BS object
    url = 'https://www.wunderground.com/dashboard/pws/%s/table/%s/%s/%s' % (station,
                                                                            date, date,
                                                                            timespan)
    r = render_page(url)
    soup = BS(r, "html.parser",)

    container = soup.find('lib-history-table')

    # Check that lib-history-table is found
    if container is None:
        raise ValueError("could not find lib-history-table in html source for %s" % url)

    # Get the timestamps and data from two separate 'tbody' tags
    all_checks = container.find_all('tbody')
    time_check = all_checks[0]
    data_check = all_checks[1]

    # Iterate through 'tr' tags and get the timestamps
    hours = []
    for i in time_check.find_all('tr'):
        trial = i.get_text()
        hours.append(trial)

    # For data, locate both value and no-value ("--") classes
    classes = ['wu-value wu-value-to', 'wu-unit-no-value ng-star-inserted']

    # Iterate through span tags and get data
    data = []
    for i in data_check.find_all('span', class_=classes):
        trial = i.get_text()
        data.append(trial)

    columns = {'5min': ['Temperature', 'Dew Point', 'Humidity', 'Wind Speed',
                        'Wind Gust', 'Pressure', 'Precip. Rate', 'Precip. Accum.'],
               'daily': ['Temperature_High', 'Temperature_Avg', 'Temperature_Low',
                         'DewPoint_High', 'DewPoint_Avg', 'DewPoint_Low',
                         'Humidity_High', 'Humidity_Avg', 'Humidity_Low',
                         'WindSpeed_High', 'WindSpeed_Avg', 'WindSpeed_Low',
                         'Pressure_High', 'Pressure_Low', 'Precip_Sum']}

    # Convert NaN values (stings of '--') to np.nan
    data_nan = [np.nan if x == '--' else x for x in data]

    # Convert list of data to an array
    data_array = np.array(data_nan, dtype=float)
    data_array = data_array.reshape(-1, len(columns[freq]))

    # Prepend date to HH:MM strings
    if freq == '5min':
        timestamps = ['%s %s' % (date, t) for t in hours]
    else:
        timestamps = hours

    # Convert to dataframe
    df = pd.DataFrame(index=timestamps, data=data_array, columns=columns[freq])
    df.index = pd.to_datetime(df.index)

    return df


def scrape_multiattempt(station, date, attempts=4, wait_time=5.0, freq='5min'):
    """Try to scrape data from Weather Underground. If there is an error on the
    first attempt, try again.

    Parameters
    ----------
        station : str
            The personal weather station ID
        date : str
            The date for which to acquire data, formatted as 'YYYY-MM-DD'
        attempts : int, default 4
            Maximum number of times to try accessing before failuer
        wait_time : float, default 5.0
            Amount of time to wait in between attempts
        freq : {'5min', 'daily'}
            Whether to download 5-minute weather observations or daily
            summaries (average, min and max for each day)

    Returns
    -------
        df : dataframe or None
            A dataframe of weather observations, with index as pd.DateTimeIndex
            and columns as the observed data
    """

    # Try to download data limited number of attempts
    for n in range(attempts):
        try:
            df = scrape_wunderground(station, date, freq=freq)
        except:
            # if unsuccessful, pause and retry
            time.sleep(wait_time)
        else:
            # if successful, then break
            break
    # If all attempts failed, return empty df
    else:
        df = pd.DataFrame()

    return df


def scrape_multidate(station, start_date, end_date, freq):
    """Given a PWS station ID and a start and end date, scrape data from Weather
        Underground for that date range and return it as a dataframe.

        Parameters
        ----------
            station : str
                The personal weather station ID
            start_date : str
                The date for which to begin acquiring data, formatted as 'YYYY-MM-DD'
            end_date : str
                The date for which to end acquiring data, formatted as 'YYYY-MM-DD'

        Returns
        -------
            df : dataframe or None
                A dataframe of weather observations, with index as pd.DateTimeIndex
                and columns as the observed data
        """
    # Convert end_date and start_date to datetime types
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    # Calculate time delta
    delta = end_date - start_date

    # Create list dates and append all days within the start and end date to dates
    dates = []
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        dates.append(day)
    dates = [date.strftime('%Y-%m-%d') for date in dates]

    # Repeat the station name in a list for as many dates are in the date range
    stations = [station] * len(dates)

    # Scrape wunderground for data from all dates in range and store in list of dateframes
    df_list = list(map(scrape_multiattempt, stations, dates, freq=freq))

    # Convert list of dataframes to one dataframe
    df = pd.concat(df_list)

    return df


if __name__ == "__main__":

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Scrape weather data from Weather Underground')
    parser.add_argument('station', type=str, help='The personal weather station ID')
    parser.add_argument('date', type=str, help='The date for which to acquire data, formatted as YYYY-MM-DD')
    parser.add_argument('freq', type=str, help='Whether to download 5-minute weather observations or '
                                               'daily summaries (average, min and max for each day)')
    args = parser.parse_args()

    df = scrape_multiattempt(args.station, args.date, freq=args.freq)

    filename = '%s_%s.csv' % (args.station, args.date)
    df.to_csv(filename)
