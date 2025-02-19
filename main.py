import os
from datetime import datetime
from marketscreener.scrapers.news_scraper import save_articles_to_csv
from marketscreener.scrapers.insider_scraper import (
    scrape_all_pages_and_save_to_csv,
    scrape_all_insiders
)
from marketscreener.scrapers.company_scraper import scrape_all_companies

current_date = datetime.now().strftime('%Y-%m-%d')


def run_news_scraper():
    print("Running News Scraper...")
    news_endpoints = ['IPO',
                      'mergers-acquisitions',
                      'rumors', 'new-contracts',
                      'appointments',
                      'share-buybacks',
                      'call-transcripts']
    file_path = f"marketscreener/data/marketscreener_articles_{current_date}.csv"  # Replace with actual file path
    if not os.path.exists(file_path):
        save_articles_to_csv(news_endpoints)
    else:
        print(f"News file {file_path} already exists. Skipping scraping.")


def run_insider_scraper():
    print("Running Insider Scraper...")
    insiders_file_path = f"marketscreener/data/insiders_{current_date}.csv"  # Replace with actual file path
    if not os.path.exists(insiders_file_path):
        scrape_all_pages_and_save_to_csv()
    full_insiders_file_path = f"marketscreener/data/full_insiders_{current_date}.csv"  # Replace with actual file path
    if not os.path.exists(full_insiders_file_path):
        scrape_all_insiders()
    else:
        print("Insider file already exists. Skipping scraping.")


def run_company_scraper():
    print("Running Company Scraper...")
    scrape_all_companies()


def run_all_scrapers():
    """
    Runs all the scrapers in sequence: news, insider, and company scrapers.
    """
    run_news_scraper()
    run_insider_scraper()
    run_company_scraper()


def main():
    print("Select which scrapers to run:")
    print("1. News")
    print("2. Insider")
    print("3. Company")
    print("4. All")
    choices = input("Enter your choices separated by commas (e.g., 1,2,3): ")
    selected_options = choices.split(',')

    if '1' in selected_options:
        run_news_scraper()
    if '2' in selected_options:
        run_insider_scraper()
    if '3' in selected_options:
        run_company_scraper()
    if '4' in selected_options:
        run_all_scrapers()


if __name__ == "__main__":
    main()