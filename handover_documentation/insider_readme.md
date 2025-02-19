# MarketScreener Insider Scraper

This project is a web scraper designed to extract insider information from the MarketScreener website. It collects data such as insider names, profile links, positions, companies, net worth, and more detailed insider profiles.

Note that the structure we have defined is due to the following flow:

1. Every insider is listed on this page [(https://www.marketscreener.com/insiders/trends/?p={page number})](https://www.marketscreener.com/insiders/trends/?p=2)
2. We iterate through all the pages containing insiders
   1. (currently 90 per page with total 37000 insiders -> Approx 410 pages)
   2. Get all 37000+ individual insider links consolidated as a csv
3. Using this list, we scrape each link to generate a row with the insider's data

## Usage

### Scrape Names and URLs

The `scrape_names_and_urls` function scrapes the names and URLs of insiders from a given page number on the MarketScreener website.

```python
scrape_names_and_urls(page_number: int)
```

- `page_number`: The page number to scrape.
- This function returns a list of tuples containing insider names and their profile URLs.

### Scrape All Pages and Save to CSV

The `scrape_all_pages_and_save_to_csv` function scrapes multiple pages of insider data and saves the results to a CSV file.

```python
scrape_all_pages_and_save_to_csv(total_pages: int = 500, start_page: int = 1)
```

- `total_pages`: Total number of pages to scrape.
- `start_page`: The page number to start scraping from.
- This function saves the scraped data to a CSV file, updating the file every 10 pages to ensure progress is saved.

### Extract Insider Information

The `extract_insider_info` function extracts detailed information about an insider from their profile page.

```python
extract_insider_info(name: str, url: str) -> dict
```

- `name`: The name of the insider.
- `url`: The URL of the insider's profile.
- This function returns a dictionary containing the insider's detailed information, such as current position, company, net worth, and more.

### Save to CSV

The `save_to_csv` function saves a list of Insider objects to a CSV file.

```python
save_to_csv(insiders_data: list[Insider], output_file: str)
```

- `insiders_data`: List of Insider objects.
- `output_file`: The name of the output CSV file.
- This function appends new data to an existing file or creates a new file if it doesn't exist.

### Scrape All Insiders

The `scrape_all_insiders` function scrapes all insiders' information from a DataFrame containing names and links, and saves it to a CSV file.

```python
scrape_all_insiders()
```

- This function processes each insider, extracts their information, and saves it to a CSV file with checkpointing every 30 entries to prevent data loss.

## Notes

- Ensure that the required libraries are installed and properly configured.
- The scraper uses a checkpoint mechanism to save progress and avoid data loss in case of interruptions.
- Duplicate entries are identified and removed based on both 'name' and 'current_company'.
- There are many helper functions that each do a specific task, one thing to note is that some insiders have multiple roles within 1 company which is currently handled but might break in the future.

# Helper Functions in insider_scraper.py

This document provides an overview of the helper functions used in the insider_scraper.py script. These functions are designed to extract specific pieces of information from HTML content using BeautifulSoup.

## Functions Overview

### 1. extract_text

Purpose: Extracts text from a specified HTML tag, optionally filtered by a search string or class.

Parameters:

* soup: The BeautifulSoup object containing the HTML content.
* tag: The HTML tag to search for.
* search_string: (Optional) A string to search for within the tag's text.
* class_: (Optional) The class attribute to filter the tag.
* default: The default value to return if extraction fails.
* is_digit: A boolean indicating if the extracted text should be a digit.

Logic:

* Searches for the specified tag, optionally filtered by search_string or class_.
* Strips and returns the text from the tag.
* If is_digit is True, returns only the first word if it's a digit.
* Returns default if extraction fails.

### 2. extract_industries

Purpose: Extracts a list of industries from the HTML content, excluding the insider's age.

Parameters:

* soup: The BeautifulSoup object containing the HTML content.
* age: The age of the insider to exclude from the results.

Logic:

* Finds all `<span>` tags with the class badge.
* Strips and collects text from these tags, excluding any that contain the insider's age or are too short.
* Returns a unique list of industries.

### 3. extract_tables

Purpose: Extracts various tables of information related to an insider, such as known holdings, positions, and trainings.

Parameters:

* soup: The BeautifulSoup object containing the HTML content.
* name: The name of the insider, used to identify specific tables.

Logic:

* Finds all `<div>` elements with the class card.
* Extracts tables from these cards, categorizing them by their headers.
* Calls specific extraction functions for known holdings, active positions, former positions, and trainings.

### 4. extract_known_holdings

Purpose: Extracts known holdings information from a specific table.

Parameters:

* tables_with_headers: A dictionary of tables categorized by their headers.

Logic:

* Looks for the table with the header 'Known holdings in public companies'.
* Extracts details such as company name, link, date, number of shares, valuation, and valuation date from each row.
* Returns a dictionary of known holdings.

### 5. extract_positions

Purpose: Extracts active or former positions from a specific table.

Parameters:

* tables_with_headers: A dictionary of tables categorized by their headers.
* key: The header key to identify the relevant table.

Logic:

* Looks for the table with the specified header key.
* Extracts company names and positions from each row.
* Filters out any rows with invalid company names.
* Returns a dictionary of positions.

### 6. extract_trainings

Purpose: Extracts training information from a specific table.

Parameters:

* tables_with_headers: A dictionary of tables categorized by their headers.
* key: The header key to identify the relevant table.

Logic:

* Looks for the table with the specified header key.
* Extracts institution names and degrees from each row.
* Returns a dictionary of trainings.

---

These helper functions are crucial for parsing and extracting structured data from the HTML content of insider profile pages. They enable the main scraping functions to efficiently gather and organize the necessary information.
