# MarketScreener Company Scraper

This project is a web scraper designed to extract company information from the MarketScreener website. It collects data such as company names, stock links, currency, sector, and detailed company profiles, including executives and governance information.

## Usage

### Extract Categories to CSV

Note that similar to the insiders page, there is a comparable one on MarketScreener that lists the different company categories from which we can scrape the list of category URLs. [(https://www.marketscreener.com/stock-exchange/sectors/)](https://www.marketscreener.com/stock-exchange/sectors/)

The `extract_categories_to_csv` function extracts category and link pairs from the MarketScreener sectors page and saves them to a CSV file.

```python
extract_categories_to_csv(output_filename: str)
```

- `output_filename`: The name of the CSV file to save the data.
- This gives us a list of links to the companies in each category

### Scrape Stock Data

The `scrape_stock_data` function scrapes stock data from a given URL and saves it to a CSV file

```python
scrape_stock_data(url: str, sector: str)
```

- `url`: The URL to scrape data from.
- `sector`: The sector name for the stocks.

  This is the toughest part to get right, since for the larger categories there are many companies, which cannot be scraped by request directly as only a limited number will show up in the initial list. The solution implemented for this function is to use selenium to act as an agent which tries to scroll down the page (forcing more companies to load) and scraping the company information in the table as they appear.

### Scrape Company Names and URLs

The `scrape_company_names_and_urls` function scrapes company names and URLs from the MarketScreener website and saves them to a CSV file.

```python
scrape_company_names_and_urls(output_filename: str)
```

* `output_filename`: The name of the CSV file to save the data.

It just runs the `extract_categories_to_csv` function, then uses the output file as a basis for which to run the `scrape_stock_data` on each category, giving us a final master list of the links to every company

### Extract Company Information

The `extract_company_info` function extracts company information from the given URL.

```python
extract_company_info(url: str, full: bool = False)
```

- `url`: The URL of the page to scrape.
- `full`: A boolean indicating whether to extract full information, including country mapping.

  This function scrapes the key information about each company from their individual pages, including:

  - company_name
  - country, ticker
  - isin
  - industry
  - sector
  - company_profile
  - executives

### Scrape All Companies

* The `scrape_all_companies` function scrapes all companies' information and saves it to a CSV file.
* It assumes that you have already run the `extract_categories_to_csv `and `scrape_company_names_and_urls `to generate the files containing all the company links in each category.
* Then, we run `extract_company_info` on each link to get the info as a row in our eventual CSV file.
* Given that there are thousands of companies, I have implemented a checkpointing system which saves the checkpoint every 30 companies scraped.

## Notes

- Ensure that the Chrome WebDriver version matches your installed Chrome browser version.
- The scraper uses a checkpoint mechanism to save progress and avoid data loss in case of interruptions.
- Duplicate entries are identified and removed based on both 'name' and 'isin'.
