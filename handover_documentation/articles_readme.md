# MarketScreener News Scraper

This script is designed to scrape news articles from the MarketScreener website. It provides functions to fetch, parse, and save article data into a CSV file.

Note that we have designed the overall main function to run based on endpoints, which are news categories, the current list of endpoints which we are scraping can be found in the function below:

```python
def run_news_scraper():
    print("Running News Scraper...")
    news_endpoints = ['IPO','mergers-acquisitions','rumors', 'new-contracts','appointments','share-buybacks','call-transcripts']
    file_path = f"marketscreener/data/marketscreener_articles_{current_date}.csv"# Replace with actual file path
    if not os.path.exists(file_path):
		save_articles_to_csv(news_endpoints)
```

Below is a detailed explanation of each function and its logic.

## Usage

### Utility Functions

```python
parse_time_string(time_str: str) -> datetime
```

* Purpose: Converts a time string into a datetime object.
* Logic:

  * Attempts to parse the input string using different date/time formats.
  * If a format matches, it constructs a datetime object using the current date or year.
  * Raises a ValueError if the string does not match any expected formats.

```python
fetch_html_content(url: str) -> str
```

* Purpose: Retrieves the HTML content of a given URL.
* Logic:

  * Sends a GET request to the URL with a random user agent.
  * Checks for request success and returns the HTML content.
  * Raises a RuntimeError if the request fails.

### Article Scraping

```python
extract_article_text(soup: BeautifulSoup) -> str
```

* Purpose: Extracts the main text of an article from a BeautifulSoup object.
* Logic:

  * Searches for a specific div class containing the article text.
  * Returns the text if found, otherwise returns a message indicating the text was not found.

```python
extract_marketscreener_article(url: str) -> str
```

* Purpose: Extracts article text from a MarketScreener article URL.
* Logic:

  * Fetches HTML content and parses it with BeautifulSoup.
  * Uses extract_article_text to get the article text.
  * Handles exceptions and returns an error message if extraction fails.

```python
get_article_from_link(article_link: str) -> dict
```

* Purpose: Retrieves article details from a given article link.
* Logic:

  * Fetches and parses HTML content.
  * Extracts article text, headline, publication date, and company link.
  * Returns a dictionary with these details or an error message if extraction fails.

```python
get_articles_from_marketscreener(url: str, category: str) -> ArticleCollection
```

* Purpose: Retrieves articles from a MarketScreener page.
* Logic:

  * Fetches and parses HTML content.
  * Iterates through tables to find article links and details.
  * Uses parse_time_string to convert publication times.
  * Collects articles into an ArticleCollection object.

```python
save_articles_to_csv(endpoint_list: list)
```

* Purpose: Retrieves articles from a list of endpoints and saves them to a CSV file.
* Logic:

  * Iterates through endpoints, fetching articles using get_articles_from_marketscreener.
  * Converts articles to a DataFrame and removes duplicates based on headlines.
  * Saves the DataFrame to a CSV file named with the current date.
