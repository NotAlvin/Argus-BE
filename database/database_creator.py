import os
import random
import time
import urllib
from datetime import datetime

import pandas as pd
import requests
import ast
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm

from utils.base_templates import Insider, Company, NewsArticle, ArticleCollection

'''
Helper functions and global variables
'''

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
    'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Mobile Safari/537.36'
    # Add more user agents as needed
]

def get_random_user_agent():
    return {'User-Agent': random.choice(USER_AGENTS)}


def complete_href(href: str) -> str:
    return f'https://www.marketscreener.com{href}'

def str_to_dict_expansion(dict_repr: any) -> dict:
    dict_repr = str(dict_repr)
    if dict_repr.strip() == '{}':
        return {}
    else:
        try:
            return ast.literal_eval(dict_repr.strip())
        except Exception as e:
            print(e)
            return {}

'''
Scraping Insiders

This module provides functions to scrape insider information from the MarketScreener website. It includes functionality to extract names and URLs of insiders, gather detailed insider information, and save the data to CSV files.

Functions:
- scrape_names_and_urls(page_number: int = 1): Scrapes the names and URLs of insiders from a given page number on the MarketScreener website.
- scrape_all_pages_and_save_to_csv(total_pages: int = 500, start_page: int = 1): Scrapes multiple pages of insider data and saves the results to a CSV file.
- extract_insider_info(name, url) -> Insider: Extracts detailed information about an insider from their profile page.
- save_to_csv(insiders_data, output_file): Saves a list of Insider objects to a CSV file.
- save_insiders_to_csv(input_file: str, output_file: str): Processes a CSV file of insider names and URLs, extracts detailed information, and saves it to another CSV file.
- extract_categories_to_csv(output_filename: str): Extracts category and link pairs from the MarketScreener sectors page and saves them to a CSV file.
'''

def scrape_names_and_urls(page_number: int):
    if page_number == 1:
        url = "https://www.marketscreener.com/insiders/trends/"
    else:
        url = f"https://www.marketscreener.com/insiders/trends/?p={page_number}"
    try:
        response = requests.get(url, headers=get_random_user_agent())
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed on page {page_number}: {e}")
        return None

    soup = BeautifulSoup(urllib.parse.unquote(response.text), 'html.parser')
    name_links = soup.find_all('a', class_='link txt-bold txt-s2')

    results = []
    for link in name_links:
        name = link.get_text(strip=True)
        href = link.get('href')
        results.append((name, href))
    return results

def scrape_all_pages_and_save_to_csv(total_pages: int = 500, start_page: int = 1):
    all_results = []
    current_date = datetime.now().strftime('%Y-%m-%d')
    output_file = f'insiders_{current_date}.csv'
    # Load existing data if the file exists
    if os.path.exists(output_file):
        df_existing = pd.read_csv(output_file)
        all_results.extend(df_existing.values.tolist())
        start_page = len(df_existing) // 20 + 1  # Assuming 20 results per page

    for page_number in range(start_page, total_pages + 1):
        print(f"Scraping page {page_number}...")
        results = scrape_names_and_urls(page_number)
        if results is None:
            print(f"Terminating at page {page_number} due to failure.")
            break
        all_results.extend(results)

        # Save progress every 10 pages
        if page_number % 10 == 0:
            df = pd.DataFrame(all_results, columns=['Name', 'Link'])
            df.to_csv(output_file, index=False)
            print(f"Progress saved up to page {page_number}")

    # Final save
    df = pd.DataFrame(all_results, columns=['Name', 'Link'])
    
    df.to_csv(output_file, index=False)
    print(f"Final data saved to {output_file}")

def extract_insider_info(name: str, url: str) -> Insider:
    response = requests.get(complete_href(url), headers=get_random_user_agent())
    response.raise_for_status()  # Raise an error for bad responses

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Initialize variables
    company_name = "N/A"
    company_url = "N/A"
    position_name = "N/A"

    # Iterate over all <p> tags with class 'm-0' to find the one with an <a> tag
    for p_tag in soup.find_all('p', class_='m-0'):
        company_tag = p_tag.find('a')
        if company_tag:
            position_name = ' '.join(p_tag.text.strip().split())
            company_name = company_tag.text.strip()
            company_url = company_tag['href']
            break

    # Extract net worth
    try:
        net_worth_tag = soup.find('p', string=lambda x: x and 'Net worth:' in x)
        net_worth = ' '.join(net_worth_tag.text.split(':', 1)[1].strip().split()) if net_worth_tag else "N/A"
    except Exception:
        net_worth = "N/A"

    # Extract age
    try:
        age_tag = soup.find('span', class_='badge')
        age = age_tag.text.strip().split()[0] if age_tag and age_tag.text.strip().split()[0].isdigit() else "N/A"
    except Exception:
        age = "N/A"

    # Extract industries
    try:
        industries_tags = soup.find_all('span', class_='badge')
        industries = list(set([tag.text.strip() for tag in industries_tags if len(tag.text.strip()) > 2 and age not in tag.text.strip()]))
    except Exception as e:
        industries = []

    # Extract summary
    try:
        summary_tag = soup.find('p', class_='mt-0 txt-justify')
        summary = summary_tag.text.strip() if summary_tag else "N/A"
    except Exception:
        summary = "N/A"

    # Find all card elements that contain both header and content
    cards = soup.find_all('div', class_='card')

    # Initialize a dictionary to store table headers and their associated HTML
    tables_with_headers = {}

    # Iterate over each card to extract the header and table
    for card in cards:
        # Find the header
        header = card.find('div', class_='card-header')
        if header:
            header_text = header.get_text(strip=True)
            
            # Find the associated table
            table = card.find('div', class_='card-content').find('table')
            if table:
                # Store the header and table HTML in the dictionary
                tables_with_headers[header_text] = table

    # Extract known holdings
    known_holdings = {}
    if 'Known holdings in public companies' in tables_with_headers.keys():
        table = tables_with_headers['Known holdings in public companies']
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) >= 5:
                a_tag = columns[0].find('a')

                # Extract the link (href attribute) and the company name (text)
                link = "N/A"
                company = "N/A"
                if a_tag:
                    link = a_tag['href']
                    company = a_tag.get_text(strip=True)

                date = columns[1].get_text(strip=True)
                number_of_shares = columns[2].get_text(strip=True)
                valuation = columns[3].get_text(strip=True)
                valuation_date = columns[4].get_text(strip=True)

                known_holdings[company] = {
                    'link': link,
                    'date': date,
                    'number_of_shares': number_of_shares,
                    'valuation': valuation,
                    'valuation_date': valuation_date
                }
                
    # Extract active and former positions
    active_positions = {}
    former_positions = {}
    if f'{name} active positions' in tables_with_headers.keys():
        table = tables_with_headers[f'{name} active positions']
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) >= 3:
                company = columns[0].find('span', class_='link').get_text(strip=True) if columns[0].find('span', class_='link') else columns[0].get_text(strip=True)
                position = columns[1].get_text(strip=True)
                if '░' not in company:
                    active_positions[company] = position

    if f'Former positions of {name}' in tables_with_headers.keys():
        table = tables_with_headers[f'Former positions of {name}']
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) >= 3:
                company = columns[0].find('span', class_='link').get_text(strip=True) if columns[0].find('span', class_='link') else columns[0].get_text(strip=True)
                position = columns[1].get_text(strip=True)
                if '░' not in company:
                    former_positions[company] = position

    # Extract trainings
    trainings = {}
    if f'Training of {name}' in tables_with_headers.keys():
        table = tables_with_headers[f'Training of {name}']
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) >= 2:
                institution = columns[0].get_text(strip=True)
                degree = columns[1].get_text(strip=True)
                trainings[institution] = degree

    # Create and return an Insider instance
    return Insider(
        name=name,
        current_position=position_name,
        current_company=company_name,
        company_url=company_url,
        net_worth=net_worth,
        known_holdings=known_holdings,
        age=age,
        industries=industries,
        summary=summary,
        active_positions=active_positions,
        former_positions=former_positions,
        trainings=trainings,
        link=url
    )

def save_to_csv(insiders_data: list[Insider], output_file: str):
    df = pd.DataFrame([insider.dict() for insider in insiders_data])
    if os.path.exists(output_file):
        df.to_csv(output_file, mode='a', header=False, index=False)
    else:
        df.to_csv(output_file, index=False)

def save_insiders_to_csv(input_file: str, output_file: str):
    # Load the existing data
    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist.")
        return

    df = pd.read_csv(input_file)
    insiders_data = []

    # Load existing insiders if the output file exists
    if os.path.exists(output_file):
        df_existing = pd.read_csv(output_file)
        processed_links = set(df_existing['link'].tolist())
    else:
        processed_links = set()

    # Iterate over the DataFrame with progress tracking
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing Insiders"):
        name, url = row['Name'], row['Link']
        # Skip already processed links
        if url in processed_links:
            continue

        try:
            # Convert row to Insider object
            insider = extract_insider_info(name, url)
            insiders_data.append(insider)
            processed_links.add(url)

            # Save progress every 10 entries
            if len(insiders_data) % 10 == 0:
                save_to_csv(insiders_data, output_file)
                insiders_data.clear()  # Clear the list after saving

        except Exception as e:
            print(f"Failed to process {name} at {url}: {e}")
            break  # Stop processing on failure

    # Final save
    if insiders_data:
        save_to_csv(insiders_data, output_file)
        print(f"Final data saved to {output_file}")

'''
Scraping Companies

This module provides functions to scrape Company information from the MarketScreener website. It includes functionality to extract names and URLs of companies, gather detailed company information, and save the data to CSV files.

Functions:
'''

def extract_categories_to_csv(output_filename: str):
    """
    Extracts category and link pairs from the given URL and saves them to a CSV file.
    
    :param url: The URL to scrape data from.
    :param output_filename: The name of the CSV file to save the data.
    """
    url = 'https://www.marketscreener.com/stock-exchange/sectors/'
    
    response = requests.get(url, headers=get_random_user_agent())
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract category and link pairs
    data = []
    for div in soup.find_all('div', class_='c-6 cm-4 cl-4 mb-15'):
        link_tag = div.find('a', href=True)
        category_tag = div.find('h2')
        if link_tag and category_tag:
            link = complete_href(link_tag['href'])
            category = category_tag.get_text(strip=True)
            data.append({'Category': category, 'Link': link})

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Save to CSV
    df.to_csv(output_filename, index=False)
    print(f"Data saved to {output_filename}")
    return output_filename

def scrape_stock_data(url: str, sector: str):
    # Set up the WebDriver (e.g., Chrome)
    driver = webdriver.Chrome()

    # Open the webpage
    driver.get(url)

    # Initialize a DataFrame to store the data
    df = pd.DataFrame(columns=['Stock Name', 'Link', 'Currency', 'Sector'])

    # Load existing data if checkpoint file exists
    checkpoint_file = 'stock_data_checkpoint.csv'
    if os.path.exists(checkpoint_file):
        df = pd.read_csv(checkpoint_file)

    # Initialize a list to store row data
    data_list = []

    # Initialize variables to track scrolling
    last_height = driver.execute_script("return document.body.scrollHeight")
    rows_extracted = len(df)

    while True:
        # Get the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all rows in the table body
        rows = soup.find_all('tr')
        
        # Check for the presence of the bottom row
        bottom_row = soup.find('tr', id='stock-screener-bottom')
        
        # Determine the starting index for new rows
        start_index = len(df)

        # Print the range of rows being scraped
        print(f'Scraping rows {start_index} to {len(rows)}')  # Exclude the bottom row
        if len(rows) > start_index:
            # Iterate over each row and extract the data, skipping the first and last row
            for row in rows[start_index:]:
                try:
                    # Extract the stock name
                    stock_name = row.find('a', class_='link link--blue table-child--middle align-top').text.strip()

                    # Extract the stock link
                    link = row.find('a', class_='link link--blue table-child--middle align-top')['href']

                    # Extract the currency
                    currency = row.find('span', class_='txt-muted c-none cm-inline').text.strip()

                    # Extract the sector
                    sector_title = row.find('div', class_='txt-inline link').get('title')

                    # Append the extracted data to the list
                    data_list.append({
                        'Stock Name': stock_name,
                        'Link': 'https://www.marketscreener.com' + link,
                        'Currency': currency,
                        'Sector': sector_title
                    })

                except AttributeError as e:
                    # Log the error for debugging
                    print(f"Error extracting data: {e}")
                    continue

        # Convert the list of dictionaries to a DataFrame and append to the main DataFrame
        if data_list:
            df = pd.concat([df, pd.DataFrame(data_list)], ignore_index=True)
            df.drop_duplicates(subset=['Link'], inplace=True)  # Remove duplicates based on 'Link'
            data_list.clear()  # Clear the list after appending

        # Save the DataFrame to a checkpoint file after each scroll
        df.to_csv(checkpoint_file, index=False)

        # Check if new rows were added
        new_rows_extracted = len(df)
        if new_rows_extracted == rows_extracted:
            break  # Exit the loop if no new rows were added
        rows_extracted = new_rows_extracted

        # Scroll down to load more rows if the bottom row is present
        if bottom_row:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(5)  # Adjust the sleep time as needed

    # Close the driver
    driver.quit()

    # Save the final DataFrame to a CSV file
    current_date = datetime.now().strftime('%Y-%m-%d')
    output_file = f"./database/companies/{sector}_{current_date}.csv"
    df.to_csv(output_file, index=False)

    # Delete the checkpoint file
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    print(f"Total rows extracted: {len(df)}")
    print(f"Data saved to {output_file}")

def scrape_company_names_and_urls(output_filename: str):
    extract_categories_to_csv(output_filename)
    stock_sectors = pd.read_csv(output_filename)
    stock_sectors.apply(lambda row: scrape_stock_data(row['url'], row['category']), axis=1)

def extract_company_info(url: str) -> dict[str, dict[str, dict[str, dict[str, str]]]]:
    """
    Extracts executives information from the given URL.

    Args:
        url (str): The URL of the page to scrape.

    Returns:
        Dict[str, Dict[str, Dict[str, Dict[str, str]]]]: A dictionary containing executives information.
    """
    # Adjust URL for contact and executives information
    url = url +  '/company-governance/'
    
    try:
        response = requests.get(url, headers=get_random_user_agent())
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return {}

    soup = BeautifulSoup(urllib.parse.unquote(response.text), 'html.parser')

    # Find the stock ticker and ISIN
    badges = soup.find_all('h2', class_='m-0 badge txt-b5 txt-s1')
    try:
        ticker = badges[0].text.strip()
    except:
        ticker = None
    try:
        isin = badges[1].text.strip()
    except:
        isin = None

    # Find the company profile text
    try:
        company_profile_div = soup.find('div', class_='mb-10 txt-justify txt-overflow-6')
        company_profile = company_profile_div.get_text(strip=True)
    except:
        company_profile = None

    # Initialize variables to store scraped data
    executives = {'Manager': {}, 'Director': {}, 'Insider': {}}

    # Extract tables and their headers
    tables = soup.find_all('div', class_='card-content')
    for table in tables:
        header_tag = table.find('tr').find('th') if table.find('tr') else None
        header_text = header_tag.get_text(strip=True) if header_tag else None
        
        if header_text in executives:
            temp_table = table.find('table')
            if temp_table:
                for tr in temp_table.find_all('tr')[1:]:  # Skip the header row
                    manager_cell = tr.find('td', {'class': 'table-child--w240 table-child--top'})
                    if manager_cell:
                        try:
                            # First attempt: Extract the manager name from the <p> tag
                            manager_name = manager_cell.find('p', class_='m-0').get_text(strip=True) if manager_cell.find('p', class_='m-0') else None
                            # Second attempt: If the first method fails, try extracting from the <span> tag
                            if not manager_name:
                                manager_name = manager_cell.find('span', class_='c').get_text(strip=True) if manager_cell.find('span', class_='c') else "N/A"
                            
                            manager_href = manager_cell.find('a')['href'] if manager_cell.find('a') else "N/A"
                        except:
                            pass
                        # Extract positions and dates
                        positions = {}
                        position_table = tr.find('table', {'class': 'table table--small table--fixed'})
                        if position_table:
                            for position_row in position_table.find_all('tr'):
                                position = position_row.find_all('td')[0].get_text(strip=True)
                                try:
                                    start_date = position_row.find_all('td')[1].get_text(strip=True)
                                    end_date = position_row.find_all('td')[2].get_text(strip=True)
                                    positions[position] = f'{start_date} until {end_date}'
                                except:
                                    start_date = position_row.find_all('td')[1].get_text(strip=True)
                                    positions[position] = start_date

                        executives[header_text][manager_name] = {
                            'href': manager_href,
                            'positions': positions
                        }
    return ticker, isin, company_profile, executives

def scrape_all_companies():
    df = pd.read_csv('database/categories_links.csv')
    companies_data = []  # List to store company data
    checkpoint_interval = 30  # Save every 30 companies
    checkpoint_file = 'database/companies_info_checkpoint.csv'

    # Outer loop with tqdm for industries
    for industry in tqdm(df['Category'], desc="Processing Industries"):
        file_path = f'database/companies/{industry}_2024-10-24.csv'
        temp_df = pd.read_csv(file_path)
        
        # Inner loop with tqdm for companies
        for i, row in tqdm(temp_df.iterrows(), total=temp_df.shape[0], desc=f"Processing Companies in {industry}", leave=False):
            name = row['Stock Name']
            sector = row['Sector']
            url = row['Link']
            ticker, isin, company_profile, executives = extract_company_info(url)
            # Append company data to the list
            companies_data.append({
                'name': name,
                'isin': isin,
                'ticker': ticker,
                'industry': industry,
                'sector': sector,
                'profile': company_profile,
                'executives': executives,
                'link': url  # Use the link as a key
            })

            # Checkpointing: Save every 30 companies
            if len(companies_data) % checkpoint_interval == 0:
                companies_df = pd.DataFrame(companies_data)
                companies_df.to_csv(checkpoint_file, index=False, mode='a', header=not os.path.exists(checkpoint_file))
                companies_data = []  # Clear the list after saving

    # Save any remaining companies after the loop
    if companies_data:
        companies_df = pd.DataFrame(companies_data)
        companies_df.to_csv(checkpoint_file, index=False, mode='a', header=not os.path.exists(checkpoint_file))
    df = pd.read_csv(checkpoint_file)
    mapping = pd.read_csv('database/country_codes_2024-11-01.csv')

    # Extract the first two characters from the 'isin' column to get the country code
    df['country_code'] = df['isin'].str[:2]

    # Create a dictionary for mapping ISO Code to Country Name (EN)
    iso_to_country = mapping.set_index('ISO Code')['Country Name (EN)'].to_dict()

    # Map the country code to the country name
    df['country'] = df['country_code'].map(iso_to_country)

    # Drop the temporary 'country_code' column if not needed
    df.drop(columns=['country_code'], inplace=True)
    df = df.drop_duplicates()
    df.to_csv(checkpoint_file, index=False)

'''
Scraping News Articles

This module provides functions to scrape News articles from the MarketScreener website.
'''

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
def get_article_from_link(article_link: str):
    soup = fetch_html_content(article_link)
    soup = BeautifulSoup(soup)
    article_content = extract_article_text(soup)
    article_headline = soup.find('title').get_text(separator='\n', strip=True)
    # Extract the date and title attributes
    span = soup.find('span', class_='js-date-relative')
    publication_date = span.get('data-utc-date')

    component_list = article_link.split('/')
    company_link = '/' + '/'.join(component_list[3:6])
    return {
        'headline': article_headline,
        'content': article_content,
        'company_link': company_link,
        'link': article_link,
        'publication_date': publication_date
    }

def get_articles_from_marketscreener(url: str) -> ArticleCollection:
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

    articles_list = []  # Initialize a list to store NewsArticle objects
    category = "MarketScreener "  # Assuming the source is MarketScreener
    extraction_date = datetime.now()  # Current date and time for extraction

    tables = soup.find_all('table')
    for table in tables:
        for row in table.find_all('tr'):
            headline_tag = row.find('a', class_='c txt-s1 txt-overflow-2 link link--no-underline my-5 my-m-0')
            if not headline_tag:
                continue

            headline = headline_tag.text.strip()
            link = 'https://www.marketscreener.com' + headline_tag.get('href')
            # Find the company link
            company_tag = row.find('a', class_='link link--blue c-flex align-top')
            company_name = company_tag.get('title') if company_tag else None
            company_link = company_tag.get('href') if company_tag else None

            source_tag = row.find('span', class_='c-block p-5 badge badge--small txt-s1')
            source = source_tag.get('title') if source_tag else source
            time_tag = row.find('span', class_='js-date-relative txt-muted h-100')
            publication_date = parse_time_string(time_tag.text.strip()) if time_tag else None

            article = NewsArticle(
                headline=headline,
                content=extract_marketscreener_article(link),
                link=link,
                company_name=company_name,
                company_link=company_link,
                source=source,
                publication_date=publication_date
            )
            articles_list.append(article)  # Append each NewsArticle to the list

    # Create and return an ArticleCollection object with all fields filled
    return ArticleCollection(
        extraction_date=extraction_date,
        articles=articles_list
    )

def save_articles_to_csv(endpoint_list, base_url, csv_file_name):
    """
    Iterates through the endpoint list, retrieves article collections, and saves them to a CSV file.
    
    Args:
        endpoint_list (list): List of endpoints to retrieve articles from.
        base_url (str): The base URL for the MarketScreener news.
        csv_file_name (str): The name of the CSV file to save the articles.
    """
    all_articles = []

    for endpoint in endpoint_list:
        url = f'{base_url}/{endpoint}/'
        articles = get_articles_from_marketscreener(url)
        
        for article in articles.articles:
            all_articles.append({
                'category': endpoint,
                'extraction_date': articles.extraction_date,
                'headline': article.headline,
                'content': article.content,
                'company_name': article.company_name,
                'company_link': article.company_link,
                'link': article.link,
                'source': article.source,
                'publication_date': article.publication_date
            })

    # Convert the list of dictionaries to a DataFrame
    df = pd.DataFrame(all_articles)

    # Save the DataFrame to a CSV file
    df.to_csv(csv_file_name, index=False)
    print(f"Data saved to {csv_file_name}")