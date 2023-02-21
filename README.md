# Scraping 5-min weather data from Weather Underground in Python


## Background
Weather Undergound stores data from over 250,000 personal weather stations across the world. Unfortunately, historical data are not easy to access. It's possible to view tables of 5-min data from a single day -- see [this example](https://www.wunderground.com/dashboard/pws/KCOCREST39/table/2021-07-25/2021-07-25/daily) from a station outside Crested Butte, Colorado -- but if you try to scrape the http using something like Python's `requests` library, the tables appear blank. 

Weather Underground has a security policy that blocks automated requests from viewing data stored in each table. This is where [Selenium WebDriver](https://www.selenium.dev/documentation/en/webdriver/) comes in. WebDriver is an toolbox for natively running web browsers, so when you render a page with WebDriver, Weather Underground thinks a regular user is accessing their website and you can access the full source code. 

## Using this package
To run the script, the first thing to do is ensure that [ChromeDriver](https://chromedriver.chromium.org/) is installed. Note that you have to match the ChromeDriver version to whichever version of Chrome is installed on your machine. It's also possible to use something other than Chrome, for example [geckodriver](https://github.com/mozilla/geckodriver/releases) for Firefox or [safaridriver](https://webkit.org/blog/6900/webdriver-support-in-safari-10/) for Safari.

Next, update the path to chromedriver in `scrape_wunderground.py`:

``` python
# Set the absolute path to chromedriver
chromedriver_path = '/path/to/chromedriver'
```

As long as BeautifulSoup and Selenium are installed, the script should work fine after that. However, there are a few important points to note about processing the data once it's downloaded:

1. All data is listed in local time. So summer data is in daylight savings time and winter data is in standard time.
2. Depending on the quality of the station, 
3. All pressure data is reported as sea-level pressure. Depending on the weather station, it may be possible to back-calculate to absolute pressure; some manufacturers (e.g., Ambient Weather WS-2902) use a constant offset whereas others (e.g., Davis Vantage Pro2) perform a more complicated barometric pressure reduction using the station's 12-hr temperature and humidity history.

## Python dependencies 
time
pandas
numpy
selenium
beautifulsoup4

## Development
Pull requests are welcome. Please let me know if you have suggestions for improvement.
