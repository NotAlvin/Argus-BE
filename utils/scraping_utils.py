import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib
from tqdm import tqdm
import dateutil.parser
from datetime import datetime, timedelta
import logging
import os
import json
from typing import Optional

from utils.base_templates import NewsArticle, ArticleCollection

headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        }

def get_article_content(url: str, source: str) -> Optional[str]:
        """Fetch and extract the article content from a given URL."""
        try:
            response = requests.get(url, headers = headers)
            response.raise_for_status()
            html_content = urllib.parse.unquote(response.text)
            soup = BeautifulSoup(html_content, 'html.parser')
            print(soup)
            # Find all paragraphs within the specified div
            if source == 'CNBC':
                article_body = soup.find('div', class_='ArticleBody-articleBody')
            else:
                article_body = soup.find('div')
            
            # Extract text from paragraphs
            if article_body:
                paragraphs = article_body.find_all('p')
                article_text = '\n'.join([para.get_text() for para in paragraphs])
                return article_text
            else:
                return None
        except:
            return None

def save_article_collection_to_db(collection: ArticleCollection, source: str) -> None:
    """
    Saves the ArticleCollection to a JSON file in a folder structure based on the current date and source.
    """
    # Get the current date in YYYY-MM-DD format
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Base directory
    base_dir = 'data/article_collections'
    
    # Create directories if they don't exist
    date_dir = os.path.join(base_dir, current_date)
    os.makedirs(date_dir, exist_ok=True)
    
    # Convert articles to a list of dictionaries
    articles_data = [article.dict() for article in collection.articles]
    
    # Save JSON file for each source
    # Create a filename based on source and current date
    filename = f"{source}_{current_date}.json"
    filepath = os.path.join(date_dir, filename)
    
    
    # Write JSON to file
    with open(filepath, 'w') as f:
        json.dump(articles_data, f, indent=4, default=str)  # `default=str` to handle datetime serialization   

def scrape_cnbc() -> ArticleCollection:
    """
    Scrape news articles from CNBC's IPO page and return them as an ArticleCollection.
    """
    url = 'https://www.cnbc.com/ipos/'
    source = 'CNBC'
    try:
        # Send a GET request to the webpage
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve the CNBC IPO page: {e}")
        return ArticleCollection(articles=[])
    
    try:
        # Parse the HTML content
        html_content = urllib.parse.unquote(response.text)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all article cards
        cards = soup.find_all('div', class_='Card-card')
        
        collection = ArticleCollection(articles=[])
        
        # Extract information from each card
        for card in tqdm(cards, desc="Processing articles"):
            title_tag = card.find('a', class_='Card-title')
            image_tag = card.find('img')
            date_tag = card.find('span', class_='Card-time')
            
            # Check if required tags are present
            if title_tag and image_tag and date_tag:
                headline = title_tag.text.strip()
                link = title_tag['href']
                date_str = date_tag.text.strip()

                # Parse date based on string format
                if 'min ago' in date_str:
                    date = datetime.now() - timedelta(minutes=int(date_str.split()[0]))
                elif 'hours ago' in date_str:
                    date = datetime.now() - timedelta(hours=int(date_str.split()[0]))
                else:
                    try:
                        date = dateutil.parser.parse(date_str)
                    except ValueError:
                        logging.warning(f"Date parsing failed for {headline}, using current date.")
                        date = None

                # Append article to collection
                collection.articles.append(
                    NewsArticle(
                        headline=headline,
                        content=get_article_content(link, source),
                        summary=None,
                        sentiment=None,
                        link=link,
                        source=source,
                        publication_date=date
                    )
                )
        save_article_collection_to_db(collection, source = source)
        return collection
    
    except Exception as e:
        logging.error(f"Error while parsing CNBC IPO page: {e}")
        return ArticleCollection(articles=[])

def scrape_ticker_information(ticker):
    # URL of the website
    url = f'https://stockanalysis.com/stocks/{ticker}/company/'

    # Send a GET request to the URL
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
        # Parse the HTML content of the page with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except:
        return None

def get_key_executives(soup, company):
    # Find the table containing key executives
    try:
        executives_table = soup.find('table', class_='mb-6')

        # Initialize lists to store names and positions
        storage = {}

        # Extract data from the table
        for row in executives_table.find_all('tr', class_='border-b border-gray-200 dark:border-dark-700'):
            cols = row.find_all('td')
            name = cols[0].text.strip()
            position = cols[1].text.strip()
            hnwi = []
            storage.add(hnwi)
        return list(storage)
    except:
        return None
    
def get_info(soup):
    try:
        def extract_info(label):
            cell = soup.find('td', text=label)
            return cell.find_next('td').text.strip() if cell else None

        country = extract_info('Country')
        industry = extract_info('Industry')
        sector = extract_info('Sector')
        return country, industry, sector
    except Exception as e:
        return None

def scrape_stockanalysis() -> ArticleCollection:
    """
    Scrapes the latest IPO news articles from StockAnalysis website.
    """
    
    url = "https://stockanalysis.com/ipos/news/"
    
    try:
        # Send a GET request to the webpage
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve the webpage: {e}")
        return ArticleCollection(articles=[])
    
    try:
        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        articles = soup.find_all('div', class_='gap-4 border-gray-300 bg-white p-4 shadow last:pb-1 last:shadow-none dark:border-dark-600 dark:bg-dark-800 sm:border-b sm:px-0 sm:shadow-none sm:last:border-b-0 lg:gap-5 sm:grid sm:grid-cols-news sm:py-6')

        collection = ArticleCollection(articles=[])
        
        # Iterate over each article to extract the required information
        for article in tqdm(articles, desc="Processing articles"):
            title_tag = article.find('h3', class_='mb-2 mt-3 text-xl font-bold leading-snug sm:order-2 sm:mt-0 sm:leading-tight')
            headline = title_tag.get_text(strip=True) if title_tag else None
            link = [a['href'] for a in article.find_all('a', href=True)][0] if article.find_all('a', href=True) else None
            time_tag = article.find('div', class_='mt-1 text-sm text-faded sm:order-1 sm:mt-0')
            publication_date = dateutil.parser.parse(time_tag['title']) if time_tag and 'title' in time_tag.attrs else None
            source = time_tag.get_text(strip=True).split('-')[1].strip() if time_tag and '-' in time_tag.get_text(strip=True) else None
            description_tag = article.find('p', class_='overflow-auto text-[0.95rem] text-light sm:order-3')
            description = description_tag.get_text(strip=True) if description_tag else None
            stocks = article.find_all('a', class_='ticker')
            company_list = [stock.get_text(strip=True) for stock in stocks]

            collection.articles.append(
                NewsArticle(
                    headline=headline,
                    content=get_article_content(link, source),
                    summary=description,
                    sentiment=None,
                    link=link,
                    source=source,
                    companies_mentioned=company_list,
                    publication_date=publication_date
                )
            )

        save_article_collection_to_db(collection, source = 'StockAnalysis')
        return collection
    
    except Exception as e:
        logging.error(f"Error while parsing the webpage: {e}")
        return ArticleCollection(articles=[])
    
