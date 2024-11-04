import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import urllib
from datetime import datetime
from utils.base_templates import NewsArticle, ArticleCollection, Company, Insider
from utils.scraping_utils import get_article_content

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) ' \
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'

HEADERS = {'User-Agent': USER_AGENT}

def convert_time_to_current_date(time_str: str) -> datetime:
    """
    Converts a time string to a datetime object with the current date or year.
    
    Args:
        time_str (str): The time string to convert, e.g., '02:55am', 'Oct. 14', or '2024-10-20'.
        
    Returns:
        datetime: A datetime object with the appropriate date and time.
    """
    try:
        # Try to parse as time with current date
        time_format = '%I:%M%p'  # Format for '02:55am'
        time_obj = datetime.strptime(time_str, time_format).time()
        current_date = datetime.now().date()
        return datetime.combine(current_date, time_obj)
    except ValueError:
        pass

    try:
        # Try to parse as month and day with current year
        date_format = '%b. %d'  # Format for 'Oct. 14'
        date_obj = datetime.strptime(time_str, date_format).date()
        current_year = datetime.now().year
        return datetime(year=current_year, month=date_obj.month, day=date_obj.day)
    except ValueError:
        pass

    try:
        # Try to parse as full date
        full_date_format = '%Y-%m-%d'  # Format for '2024-10-20'
        return datetime.strptime(time_str, full_date_format)
    except ValueError:
        raise ValueError(f"Time string '{time_str}' does not match expected formats.")

def get_articles_from_marketinsights_table(url: str) -> ArticleCollection:
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return ArticleCollection()  # Return an empty ArticleCollection

    soup = BeautifulSoup(urllib.parse.unquote(response.text), 'html.parser')
    articles = ArticleCollection()
    
    # Corrected the table selection logic
    tables = soup.find_all('table')
    for table in tables:
        for row in table.find_all('tr'):
            # Extract the headline
            headline_tag = row.find('a', class_='c txt-s1 txt-overflow-2 link link--no-underline my-5 my-m-0')
            headline = headline_tag.text.strip() if headline_tag else None

            # Extract the link
            link = 'https://www.marketscreener.com' + headline_tag.get('href') if headline_tag else None

            # Extract the source
            source_tag = row.find('span', class_='c-block p-5 badge badge--small txt-s1')
            source = source_tag.get('title') if source_tag else None

            # Extract the publication date
            time_tag = row.find('span', class_='js-date-relative txt-muted h-100')
            publication_date = convert_time_to_current_date(time_tag.text.strip())
            if headline:
                article = NewsArticle(
                    headline=headline,
                    link=link,
                    source=source,
                    publication_date=publication_date
                )
                articles.articles.append(article)

    return articles

def scrape_company_page(url, context='Contact'):
    if context == "People":
        url = url.split('news')[0] + 'company-governance/'
    else:
        url = url.split('news')[0] + 'company/'

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

    return BeautifulSoup(urllib.parse.unquote(response.text), 'html.parser')

def get_company_sector(soup):
    if not soup:
        return 'Unknown'

    card_headers = soup.find_all('div', class_='card-header')
    for card_header in card_headers:
        title_text = card_header.get_text(strip=True)
        if title_text == 'Sector':
            card_content = card_header.find_next_sibling('div', class_='card-content')
            if card_content:
                sector_details = list(map(lambda x: x.strip(), card_content.get_text().split('\n')))
                for sector in sector_details:
                    if sector:
                        return sector
    return 'Unknown'

def get_company_contact_information(soup):
    if not soup:
        return {}

    result = {}
    company_details_section = soup.find_all('div', class_='card mb-15 pos-next')
    for company_details in company_details_section:
        try:
            company_name = company_details.find('h3', class_='card-title').text.replace('Company details: ', '')
            company_info = company_details.find_all('p', class_='m-0')
            address = company_info[1].text if len(company_info) > 1 else ''
            city_state = company_info[2].text if len(company_info) > 2 else ''
            phone = company_info[3].text if len(company_info) > 3 else ''
            website = company_details.find('a', class_='m-0')['href'] if company_details.find('a', class_='m-0') else ''

            result['Company Name'] = company_name
            result['Address Line 1'] = address
            result['Address Line 2'] = city_state
            result['Phone Number'] = phone
            result['Website'] = website
        except (IndexError, AttributeError) as e:
            print(f"Error parsing contact information: {e}")
            continue
    return result

def get_company_executives(soup):
    """
    Scrapes tables from the BeautifulSoup object and returns structured data.
    """
    if not soup:
        return []

    to_find = {'Manager': None, 'Director': None, 'Insider': None}
    tables = soup.find_all('div', class_='card-content')
    structured_data = []

    for table in tables:
        title = table.find('tr').find('th').get_text(strip=True) if table.find('tr') else None
        if title in to_find:
            temp_table = table.find('table')
            rows = temp_table.find('tbody').find_all('tr') if temp_table else []
            structured_data.append(rows)

    data = []
    for result_set in structured_data:
        for row in result_set:
            person_info = row.find('td', class_='table-child--w240 table-child--top')
            if person_info:
                name_tag = person_info.find('p', class_='m-0')
                age_tag = person_info.find('p', class_='m-0 txt-muted')
                name = name_tag.get_text(strip=True) if name_tag else ''
                age = age_tag.get_text(strip=True) if age_tag else ''

                roles_table = row.find('td', class_='table-child--top').find_next('table')
                if roles_table:
                    roles_rows = roles_table.find_all('tr')
                    for roles_row in roles_rows:
                        role = roles_row.find('td', class_='table-child--w240').get_text(strip=True)
                        date = roles_row.find('td', class_='table-child--right table-child--w80').get_text(strip=True)
                        data.append({
                            'Name': name,
                            'Age': age,
                            'Position': role,
                            'Date': date
                        })

    return data

def scrape_company_info(article):
    contact_info_soup = scrape_company_page(article.link)
    executives_soup = scrape_company_page(article.link, context = "People")
    if contact_info_soup:
        contact_info = get_company_contact_information(contact_info_soup)
        sector = get_company_sector(contact_info_soup)
    
    if executives_soup:
        executives = get_company_executives(executives_soup)

        company_name = contact_info.get('Company Name')
        if company_name:
            company = Company(
                name=company_name,
                #isin=isin,
                #ticker=ticker,
                #industry=industry,
                sector=sector,
                executives=[
                ]
            )
            article.companies_mentioned = [company]
        else:
            article.companies_mentioned = []

def scrape_main_page_marketinsights():
    endpoint_list = ['IPO', 'mergers-acquisitions', 'rumors']
    collection = ArticleCollection(articles=[])
    companies = []

    for endpoint in endpoint_list:
        url = f'https://www.marketscreener.com/news/companies/{endpoint}/'
        articles = marketinsights_table(url)
        if articles:  # Check if articles were found
            collection.articles.extend(articles)

    for article in collection.articles:
        article.content = get_article_content(article.link, article.source)
        scrape_company_info(article)
        if article.companies_mentioned:  # Check if companies were mentioned
            companies.extend(article.companies_mentioned)

    if not collection.articles:
        print("No articles found.")
    if not companies:
        print("No companies mentioned.")

    return collection, companies

if __name__ == "__main__":
    article_collection, company_list = scrape_main_page_marketinsights()
    current_date = datetime.now().strftime("%Y-%m-%d")
    directory = f"./data/article_collections/{current_date}"
    article_output_path = f"{directory}/marketinsights_articles_{current_date}.json"
    company_output_path = f"{directory}/marketinsights_companies_{current_date}.json"

    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Save the article collection to a JSON file
    with open(article_output_path, 'w') as f:
        f.write(article_collection.model_dump_json(indent=4))

    # Save the company list to a JSON file
    with open(company_output_path, 'w') as f:
        f.write(pd.DataFrame([company.dict() for company in company_list]).to_json(orient='records', indent=4))