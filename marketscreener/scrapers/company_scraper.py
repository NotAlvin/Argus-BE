import os
import time
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm
import urllib
from marketscreener.scrapers.scraping_utils import get_random_user_agent, complete_href
from utils.base_templates import Company


def extract_categories_to_csv(output_filename: str):
    """
    Extracts category and link pairs from the MarketScreener sectors page and saves them to a CSV file.

    :param output_filename: The name of the CSV file to save the data.
    """
    url = 'https://www.marketscreener.com/stock-exchange/sectors/'

    try:
        response = requests.get(url, headers=get_random_user_agent())
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching categories: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")

    data = []
    for div in soup.find_all('div', class_='c-6 cm-4 cl-4 mb-15'):
        link_tag = div.find('a', href=True)
        category_tag = div.find('h2')
        if link_tag and category_tag:
            link = complete_href(link_tag['href'])
            category = category_tag.get_text(strip=True)
            data.append({'Category': category, 'Link': link})

    df = pd.DataFrame(data)
    df.to_csv(output_filename, index=False)
    print(f"Data saved to {output_filename}")


def scrape_stock_data(url: str, sector: str):
    """
    Scrapes stock data from a given URL and saves it to a CSV file.

    :param url: The URL to scrape data from.
    :param sector: The sector name for the stocks.
    """
    driver = webdriver.Chrome()
    driver.get(url)

    df = pd.DataFrame(columns=['Stock Name', 'Link', 'Currency', 'Sector'])
    checkpoint_file = 'stock_data_checkpoint.csv'
    if os.path.exists(checkpoint_file):
        df = pd.read_csv(checkpoint_file)

    data_list = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    rows_extracted = len(df)

    while True:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        rows = soup.find_all('tr')
        bottom_row = soup.find('tr', id='stock-screener-bottom')
        start_index = len(df)

        print(f'Scraping rows {start_index} to {len(rows)}')
        if len(rows) > start_index:
            for row in rows[start_index:]:
                try:
                    stock_name = row.find('a', class_='link link--blue table-child--middle align-top').text.strip()
                    link = row.find('a', class_='link link--blue table-child--middle align-top')['href']
                    currency = row.find('span', class_='txt-muted c-none cm-inline').text.strip()
                    sector_title = row.find('div', class_='txt-inline link').get('title')

                    data_list.append({
                        'Stock Name': stock_name,
                        'Link': 'https://www.marketscreener.com' + link,
                        'Currency': currency,
                        'Sector': sector_title
                    })

                except AttributeError as e:
                    print(f"Error extracting data: {e}")
                    continue

        if data_list:
            df = pd.concat([df, pd.DataFrame(data_list)], ignore_index=True)
            df.drop_duplicates(subset=['Link'], inplace=True)
            data_list.clear()

        df.to_csv(checkpoint_file, index=False)

        new_rows_extracted = len(df)
        if new_rows_extracted == rows_extracted:
            break
        rows_extracted = new_rows_extracted

        if bottom_row:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(5)

    driver.quit()

    current_date = datetime.now().strftime('%Y-%m-%d')
    output_file = f"marketscreener/companies/{sector}_{current_date}.csv"
    df.to_csv(output_file, index=False)

    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    print(f"Total rows extracted: {len(df)}")
    print(f"Data saved to {output_file}")


def scrape_company_names_and_urls(output_filename: str):
    """
    Scrapes company names and URLs from the MarketScreener website and saves them to a CSV file.

    :param output_filename: The name of the CSV file to save the data.
    """
    extract_categories_to_csv(output_filename)
    stock_sectors = pd.read_csv(output_filename)
    stock_sectors.apply(lambda row: scrape_stock_data(row['Link'], row['Category']), axis=1)


def extract_company_info(url: str, full: bool = False):
    """
    Extracts company information from the given URL.

    :param url: The URL of the page to scrape.
    :return: A tuple containing company name, ticker, ISIN, profile, and executives.
    """
    url = url + '/company-governance/'

    try:
        response = requests.get(url, headers=get_random_user_agent())
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None, None, None, None, None, None, None, {}

    soup = BeautifulSoup(response.text, 'html.parser')

    company_name = soup.find('h1').text.split('Governance')[-1].strip().upper()
    badges = soup.find_all('h2', class_='m-0 badge txt-b5 txt-s1')
    ticker = badges[0].text.strip() if badges else None
    isin = badges[1].text.strip() if len(badges) > 1 else None
    industry_badges = soup.find_all('a', class_='badge')
    industry, sector = None, None

    for badge in industry_badges:
        # Extract the href attribute
        sector = badge.find('h2').get_text(strip=True)
        href = badge.get('href', '')
        # Parse the URL to extract the path
        path = urllib.parse.urlparse(href).path
        # Split the path and extract the relevant parts
        path_parts = path.split('/')
        # Check if 'sectors' is in the path and extract the industry
        if 'sectors' in path_parts:
            industry_index = path_parts.index('sectors') + 2
            if industry_index < len(path_parts):
                industry = path_parts[industry_index].replace('-', ' ').title().strip()

    try:
        company_profile_div = soup.find('div', class_='mb-10 txt-justify txt-overflow-6')
        company_profile = company_profile_div.get_text(strip=True)
    except:
        company_profile = None

    executives = {'Manager': {}, 'Director': {}, 'Insider': {}}
    tables = soup.find_all('div', class_='card-content')
    for table in tables:
        header_tag = table.find('tr').find('th') if table.find('tr') else None
        header_text = header_tag.get_text(strip=True) if header_tag else None
        
        if header_text in executives:
            temp_table = table.find('table')
            if temp_table:
                for tr in temp_table.find_all('tr')[1:]:
                    manager_cell = tr.find('td', {'class': 'table-child--w240 table-child--top'})
                    if manager_cell:
                        try:
                            manager_name = manager_cell.find('p', class_='m-0').get_text(strip=True) if manager_cell.find('p', class_='m-0') else None
                            if not manager_name:
                                manager_name = manager_cell.find('span', class_='c').get_text(strip=True) if manager_cell.find('span', class_='c') else "N/A"
                            
                            manager_href = manager_cell.find('a')['href'] if manager_cell.find('a') else "N/A"
                        except:
                            pass
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
    if isin is not None and full:
        mapping = pd.read_csv('marketscreener/data/country_codes_2024-11-01.csv')

        country_code = isin[:2]
        iso_to_country = mapping.set_index('ISO Code')['Country Name (EN)'].to_dict()
        # Map the country code to the country name
        country = iso_to_country.get(country_code, None)
    else:
        country = None
    return company_name, country, ticker, isin, industry, sector, company_profile, executives

def scrape_all_companies():
    """
    Scrapes all companies' information and saves it to a CSV file.
    """
    df = pd.read_csv('marketscreener/data/categories_links.csv')
    companies_data = []
    checkpoint_interval = 30
    checkpoint_file = 'marketscreener/data/companies_info_checkpoint.csv'

    for industry in tqdm(df['Category'], desc="Processing Industries"):
        file_path = f'marketscreener/companies/{industry}_2024-10-24.csv'
        temp_df = pd.read_csv(file_path)
        
        for i, row in tqdm(temp_df.iterrows(), total=temp_df.shape[0], desc=f"Processing Companies in {industry}", leave=False):
            name = row['Stock Name'].strip()
            sector = row['Sector'].strip()
            url = row['Link'].strip()
            company_name, country, ticker, isin, industry_2, sector_2, company_profile, executives = extract_company_info(url) # Chose not to use duplicated info, can be used for checking and verification instead
            try:
                assert company_name == name # Ensure that scraping is consistent
            except:
                print(f'Error with {company_name}, scraped {name} instead')
            finally:
                company = Company(
                    name=name,
                    isin=isin,
                    ticker=ticker,
                    industry=industry,
                    sector=sector,
                    profile=company_profile,
                    executives=executives,
                    link=url
                )
                companies_data.append(company.model_dump())

            if len(companies_data) % checkpoint_interval == 0:
                companies_df = pd.DataFrame(companies_data)
                companies_df.to_csv(checkpoint_file, index=False, mode='a', header=not os.path.exists(checkpoint_file))
                companies_data = []

    if companies_data:
        companies_df = pd.DataFrame(companies_data)
        companies_df.to_csv(checkpoint_file, index=False, mode='a', header=not os.path.exists(checkpoint_file))

    df = pd.read_csv(checkpoint_file)
    mapping = pd.read_csv('marketscreener/data/country_codes_2024-11-01.csv')

    df['country_code'] = df['isin'].str[:2]
    iso_to_country = mapping.set_index('ISO Code')['Country Name (EN)'].to_dict()
    df['country'] = df['country_code'].map(iso_to_country)
    df.drop(columns=['country_code'], inplace=True)

    # Identify and print duplicate entries based on both 'name' and 'isin'
    duplicate_entries = df[df.duplicated(subset=['name', 'isin'], keep=False)]

    if not duplicate_entries.empty:
        print("Duplicate Entries Found:")
        print(duplicate_entries[['name', 'isin']].value_counts())

    # Drop duplicates based on both 'name' and 'isin'
    df = df.drop_duplicates(subset=['name', 'isin'])
    
    # Save final output to a new file with the current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    final_output_file = f'marketscreener/data/companies_info_{current_date}.csv'
    df.to_csv(final_output_file, index=False)

    # Remove the checkpoint file
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)