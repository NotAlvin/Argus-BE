import requests
import urllib
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
from marketscreener.scrapers.scraping_utils import get_random_user_agent
from utils.base_templates import NewsArticle, ArticleCollection
from tqdm import tqdm

def parse_time_string(time_str: str) -> datetime:
    """
    Parses a time string into a datetime object with the current date or year.

    Args:
        time_str (str): The time string to convert, e.g., '02:55am', 'Oct. 14', or '2024-10-20'.

    Returns:
        datetime: A datetime object with the appropriate date and time.
    """
    formats = [
        ('%I:%M%p', lambda t: datetime.combine(datetime.now().date(), t.time())),
        ('%b. %d', lambda d: datetime(datetime.now().year, d.month, d.day)),
        ('%Y-%m-%d', lambda d: d)
    ]

    for fmt, constructor in formats:
        try:
            parsed_date = datetime.strptime(time_str, fmt)
            return constructor(parsed_date)
        except ValueError:
            continue

    raise ValueError(f"Time string '{time_str}' does not match expected formats.")

def fetch_html_content(url: str) -> str:
    """
    Fetches and returns the HTML content of a given URL.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: The HTML content of the page.
    """
    try:
        response = requests.get(url, headers=get_random_user_agent())
        response.raise_for_status()
        return urllib.parse.unquote(response.text)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch URL {url}: {e}")

def extract_article_text(soup: BeautifulSoup) -> str:
    """
    Extracts the article text from a BeautifulSoup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the HTML content.

    Returns:
        str: The extracted article text.
    """
    article_div = soup.find('div', class_='txt-s4 article-text')
    if not article_div:
        return 'Article text not found in the provided URL'
    return article_div.get_text(separator='\n', strip=True)

def extract_marketscreener_article(url: str) -> str:
    """
    Extracts the article text from a MarketScreener article URL.

    Args:
        url (str): The URL of the MarketScreener article.

    Returns:
        str: The extracted article text.
    """
    try:
        html_content = fetch_html_content(url)
        soup = BeautifulSoup(html_content, 'html.parser')
        return extract_article_text(soup)
    except Exception as e:
        return f'Error with extracting article text: {e}'

def get_article_from_link(article_link: str) -> dict:
    """
    Retrieves article details from a given article link.

    Args:
        article_link (str): The URL of the article.

    Returns:
        dict: A dictionary containing article details.
    """
    try:
        html_content = fetch_html_content(article_link)
        soup = BeautifulSoup(html_content, 'html.parser')
        article_content = extract_article_text(soup)
        article_headline = soup.find('title').get_text(separator='\n', strip=True)
        span = soup.find('span', class_='js-date-relative')
        publication_date = span.get('data-utc-date') if span else None

        component_list = article_link.split('/')
        company_link = '/' + '/'.join(component_list[3:6])

        return {
            'headline': article_headline,
            'content': article_content,
            'company_link': company_link,
            'link': article_link,
            'publication_date': publication_date
        }
    except Exception as e:
        return {'error': f"Failed to extract article from {article_link}: {e}"}

def get_articles_from_marketscreener(url: str, category: str) -> ArticleCollection:
    """
    Retrieves articles from a MarketScreener page.

    Args:
        url (str): The URL of the MarketScreener page.

    Returns:
        ArticleCollection: A collection of articles extracted from the page.
    """
    try:
        html_content = fetch_html_content(url)
        soup = BeautifulSoup(html_content, 'html.parser')
    except RuntimeError as e:
        print(e)
        return ArticleCollection()

    articles_list = []
    extraction_date = datetime.now()

    tables = soup.find_all('table')
    for table in tables:
        for row in table.find_all('tr'):
            headline_tag = row.find('a', class_='c txt-s1 txt-overflow-2 link link--no-underline my-5 my-m-0')
            if not headline_tag:
                continue

            headline = headline_tag.text.strip()
            link = 'https://www.marketscreener.com' + headline_tag.get('href')
            company_tag = row.find('a', class_='link link--blue c-flex align-top')
            company_name = company_tag.get('title') if company_tag else None
            company_link = company_tag.get('href') if company_tag else None

            source_tag = row.find('span', class_='c-block p-5 badge badge--small txt-s1')
            source = source_tag.get('title') if source_tag else None
            time_tag = row.find('span', class_='js-date-relative txt-muted h-100')
            publication_date = parse_time_string(time_tag.text.strip()) if time_tag else None

            article = NewsArticle(
                category=category,
                headline=headline,
                content=extract_marketscreener_article(link),
                link=link,
                company_name=company_name,
                company_link=company_link,
                source=source,
                publication_date=publication_date
            )
            articles_list.append(article)

    return ArticleCollection(
        extraction_date=extraction_date,
        articles=articles_list
    )

def save_articles_to_csv(endpoint_list: list):
    """
    Iterates through the endpoint list, retrieves article collections, and saves them to a CSV file.

    Args:
        endpoint_list (list): List of endpoints to retrieve articles from.
        base_url (str): The base URL for the MarketScreener news.
        csv_file_name (str, optional): The name of the CSV file to save the articles. Defaults to None.
    """
    base_url = 'https://www.marketscreener.com/news/companies/'

    all_articles = [
        article.dict()
        for endpoint in tqdm(endpoint_list, desc="Processing Endpoints")
        for article in get_articles_from_marketscreener(f'{base_url}{endpoint}/', endpoint).articles
    ]

    # Convert to DataFrame and remove duplicates based on the headline
    df = pd.DataFrame(all_articles)
    df.drop_duplicates(subset='headline', inplace=True)


    current_date = datetime.now().strftime('%Y-%m-%d')
    csv_file_name = f"marketscreener/data/marketscreener_articles_{current_date}.csv"
    df.to_csv(csv_file_name, index=False)
    print(f"Data saved to {csv_file_name}")