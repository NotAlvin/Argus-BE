## Overview

This document provides an overview of how the` find_company_and_insiders_from_article` and `generate_markdown_report` functions work together to generate a markdown report from a given article link. These functions are part of a data processing pipeline that extracts information about companies and insiders from articles and formats it into a structured report.

Originally something like this could be used as a structure to create an explore page in OneGlance, where we display news articles that contain liquidity event information and identify the companies and insiders that might be affected from there. The identified insiders could then be 

## Functions

```python
find_company_and_insiders_from_article
```

Purpose: This function retrieves and processes data related to a specific article, including the associated company and its insiders.

Steps:

* Fetch Article: The function first attempts to retrieve the article from a database using the provided article link. If the article is not found, it tries to scrape the article from the web.
* Fetch Company: It then retrieves the company linked to the article. If the company is not found in the database, it scrapes the company's information from the web.
* Fetch Insiders: The function extracts executive links from the company data and uses these links to fetch insider information from the database. If insiders are not found, it scrapes their information.
* Return Data: The function returns a dictionary containing the article, company, and insiders data.

```python
generate_markdown_report
```

Purpose: This function generates a markdown report using the data retrieved by find_company_and_insiders_from_article.

Steps:

* Fetch Data: It calls `find_company_and_insiders_from_article` to get the article, company, and insiders data.
* Create Directory: Ensures the output directory exists for saving the report.
* Generate File Name: Constructs a file name using the article's headline and publication date.
* Write Report: Writes the article, company, and insiders information into a markdown file. The report includes sections for the article content, company information, and linked insiders, detailing their roles, known holdings, and other relevant data.
* Save Report: The markdown report is saved to the specified directory.

## Usage

To generate a report, simply call the generate_markdown_report function with the desired article link. The function will handle data retrieval and report generation, saving the output as a markdown file in the specified directory.

```python
generate_markdown_report("https://www.marketscreener.com/quote/stock/DRUGS-MADE-IN-AMERICA-ACQ-180938395/news/Drugs-Made-In-America-Acquisition-Announces-Closing-Of-Full-Exercise-Of-IPO-Over-Allotment-Option-49092635/")
```

This will produce a markdown file containing a detailed report of the [article](https://www.marketscreener.com/quote/stock/DRUGS-MADE-IN-AMERICA-ACQ-180938395/news/Drugs-Made-In-America-Acquisition-Announces-Closing-Of-Full-Exercise-Of-IPO-Over-Allotment-Option-49092635/), the associated company, and its insiders.

## Conclusion

These functions work in tandem to automate the process of extracting and reporting on company and insider information from articles, providing a structured and easily readable markdown report.
