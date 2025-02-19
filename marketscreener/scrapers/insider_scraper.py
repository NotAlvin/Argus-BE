import os
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from marketscreener.scrapers.scraping_utils import get_random_user_agent, complete_href
from utils.base_templates import Insider

def scrape_names_and_urls(page_number: int):
    """
    Scrapes the names and URLs of insiders from a given page number on the MarketScreener website.

    :param page_number: The page number to scrape.
    :return: A list of tuples containing insider names and their profile URLs.
    """
    url = f"https://www.marketscreener.com/insiders/trends/?p={page_number}" if page_number > 1 else "https://www.marketscreener.com/insiders/trends/"
    try:
        response = requests.get(url, headers=get_random_user_agent())
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed on page {page_number}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    name_links = soup.find_all('a', class_='link txt-bold txt-s2')

    return [(link.get_text(strip=True), link.get('href')) for link in name_links]

def scrape_all_pages_and_save_to_csv(total_pages: int = 500, start_page: int = 1):
    """
    Scrapes multiple pages of insider data and saves the results to a CSV file.

    :param total_pages: Total number of pages to scrape.
    :param start_page: The page number to start scraping from.
    """
    all_results = []
    current_date = datetime.now().strftime('%Y-%m-%d')
    output_file = f'marketscreener/data/insiders_{current_date}.csv'

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

        if page_number % 10 == 0:
            pd.DataFrame(all_results, columns=['name', 'link']).to_csv(output_file, index=False)
            print(f"Progress saved up to page {page_number}")

    pd.DataFrame(all_results, columns=['name', 'link']).to_csv(output_file, index=False)
    print(f"Final data saved to {output_file}")

def extract_insider_info(name: str, url: str) -> dict:
    """
    Extracts detailed information about an insider from their profile page.

    :param name: The name of the insider.
    :param url: The URL of the insider's profile.
    :return: A dictionary containing the insider's information.
    """
    try:
        response = requests.get(complete_href(url), headers=get_random_user_agent())
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching insider info for {name}: {e}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract information
    company_name, company_url, position_name = "N/A", "N/A", "N/A"
    for p_tag in soup.find_all('p', class_='m-0'):
        company_tag = p_tag.find('a')
        if company_tag:
            position_name = ' '.join(p_tag.text.strip().split())
            company_name = company_tag.text.strip()
            company_url = company_tag['href']
            break

    net_worth = extract_text(soup, 'p', 'Net worth:', default="N/A").replace('Net worth:', '')
    age = extract_text(soup, 'span', class_='badge', default="N/A", is_digit=True)
    industries = extract_industries(soup, age)
    summary = extract_text(soup, 'p', class_='mt-0 txt-justify', default="N/A")

    known_holdings, active_positions, former_positions, trainings = extract_tables(soup, name)

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
    ).dict()

def save_to_csv(insiders_data: list[Insider], output_file: str):
    """
    Saves a list of Insider objects to a CSV file.

    :param insiders_data: List of Insider objects.
    :param output_file: The name of the output CSV file.
    """
    df = pd.DataFrame([insider.dict() for insider in insiders_data])
    if os.path.exists(output_file):
        df.to_csv(output_file, mode='a', header=False, index=False)
    else:
        df.to_csv(output_file, index=False)

def scrape_all_insiders():
    """
    Scrapes all insiders' information from a DataFrame containing names and links, and saves it to a CSV file.

    :param df: DataFrame with columns 'name' and 'link'.
    """
    current_date = datetime.now().strftime('%Y-%m-%d')
    df = pd.read_csv(f'marketscreener/data/insiders_{current_date}.csv')

    insiders_data = []
    checkpoint_interval = 30
    checkpoint_file = f'marketscreener/data/insiders_info_checkpoint.csv'

    for i, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing Insiders"):
        name = row['name']
        url = row['link']
        insider = extract_insider_info(name, url)
        insiders_data.append(insider)

        if len(insiders_data) % checkpoint_interval == 0:
            insiders_df = pd.DataFrame(insiders_data)
            insiders_df.to_csv(checkpoint_file, index=False, mode='a', header=not os.path.exists(checkpoint_file))
            insiders_data = []

    if insiders_data:
        insiders_df = pd.DataFrame(insiders_data)
        insiders_df.to_csv(checkpoint_file, index=False, mode='a', header=not os.path.exists(checkpoint_file))

    df = pd.read_csv(checkpoint_file)

    # Identify and print duplicates based on both names and companies
    duplicate_entries = df[df.duplicated(subset=['name', 'company'], keep=False)]

    if not duplicate_entries.empty:
        print("Duplicate Name-Company Pairs Found:")
        print(duplicate_entries[['name', 'current_company']].value_counts())

    df = df.drop_duplicates(subset=['name', 'current_company'])
    
    # Save final output to a new file with the current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    final_output_file = f'marketscreener/data/insiders_info_{current_date}.csv'
    df.to_csv(final_output_file, index=False)

    # Remove the checkpoint file
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

def scrape_all_company_insiders():
    """
    Scrapes all insiders' information and saves it to a CSV file.
    """
    current_date = datetime.now().strftime('%Y-%m-%d')
    df = pd.read_csv(f'marketscreener/data/insiders_{current_date}.csv')
    insiders_data = []
    checkpoint_interval = 30
    checkpoint_file = f'marketscreener/data/insiders_info_checkpoint.csv'

    for company in tqdm(df['Company'], desc="Processing Companies"):
        file_path = f'marketscreener/data/{company}_2024-10-24.csv'
        temp_df = pd.read_csv(file_path)
        
        for i, row in tqdm(temp_df.iterrows(), total=temp_df.shape[0], desc=f"Processing Insiders in {company}", leave=False):
            name = row['name']
            url = row['link']
            insider = extract_insider_info(name, url)
            insiders_data.append(insider)

            if len(insiders_data) % checkpoint_interval == 0:
                insiders_df = pd.DataFrame(insiders_data)
                insiders_df.to_csv(checkpoint_file, index=False, mode='a', header=not os.path.exists(checkpoint_file))
                insiders_data = []

    if insiders_data:
        insiders_df = pd.DataFrame(insiders_data)
        insiders_df.to_csv(checkpoint_file, index=False, mode='a', header=not os.path.exists(checkpoint_file))

    df = pd.read_csv(checkpoint_file)

    # Identify and print duplicates based on both names and companies
    duplicate_entries = df[df.duplicated(subset=['name', 'company'], keep=False)]

    if not duplicate_entries.empty:
        print("Duplicate Name-Company Pairs Found:")
        print(duplicate_entries[['name', 'company']].value_counts())

    df = df.drop_duplicates(subset=['name', 'company'])
    
    # Save final output to a new file with the current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    final_output_file = f'marketscreener/data/insiders_info_{current_date}.csv'
    df.to_csv(final_output_file, index=False)

    # Remove the checkpoint file
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

# Helper functions
def extract_text(soup, tag, search_string=None, class_=None, default=None, is_digit=False):
    try:
        if search_string:
            tag = soup.find(tag, string=lambda x: x and search_string in x)
        elif class_:
            tag = soup.find(tag, class_=class_)
        if tag:
            text = tag.text.strip()
            if is_digit and text.split()[0].isdigit():
                return text.split()[0]
            return text
    except Exception:
        pass
    return default

def extract_industries(soup, age):
    try:
        industries_tags = soup.find_all('span', class_='badge')
        return list(set([tag.text.strip() for tag in industries_tags if len(tag.text.strip()) > 2 and age not in tag.text.strip()]))
    except Exception:
        return []

def extract_tables(soup, name):
    tables_with_headers = {}
    for card in soup.find_all('div', class_='card'):
        header = card.find('div', class_='card-header')
        if header:
            header_text = header.get_text(strip=True)
            table = card.find('div', class_='card-content').find('table')
            if table:
                tables_with_headers[header_text] = table

    known_holdings = extract_known_holdings(tables_with_headers)
    active_positions = extract_positions(tables_with_headers, f'{name} active positions')
    former_positions = extract_positions(tables_with_headers, f'Former positions of {name}')
    trainings = extract_trainings(tables_with_headers, f'Training of {name}')

    return known_holdings, active_positions, former_positions, trainings

def extract_known_holdings(tables_with_headers):
    known_holdings = {}
    if 'Known holdings in public companies' in tables_with_headers:
        table = tables_with_headers['Known holdings in public companies']
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) >= 5:
                a_tag = columns[0].find('a')
                link = a_tag['href'] if a_tag else "N/A"
                company = a_tag.get_text(strip=True) if a_tag else "N/A"
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
    return known_holdings

def extract_positions(tables_with_headers, key):
    positions = {}
    if key in tables_with_headers:
        table = tables_with_headers[key]
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) >= 3:
                company = columns[0].find('span', class_='link').get_text(strip=True) if columns[0].find('span', class_='link') else columns[0].get_text(strip=True)
                position = columns[1].get_text(strip=True)
                if '░' not in company:
                    positions[company] = position
    return positions

def extract_trainings(tables_with_headers, key):
    trainings = {}
    if key in tables_with_headers:
        table = tables_with_headers[key]
        for row in table.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) >= 2:
                institution = columns[0].get_text(strip=True)
                degree = columns[1].get_text(strip=True)
                trainings[institution] = degree
    return trainings