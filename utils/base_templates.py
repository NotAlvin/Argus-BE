from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class NewsArticle(BaseModel):
    headline: str = Field(
        description="The headline of the news article",
        example="Apple Inc. Reports Record Quarterly Earnings"
    )
    content: Optional[str] = Field(
        default=None,
        description="The full content of the news article",
        example="Apple Inc. has reported record earnings for the quarter, with revenue up by 20%..."
    )
    summary: Optional[str] = Field(
        default=None,
        description="A brief summary of the news article",
        example="Apple's quarterly earnings have exceeded expectations, driven by strong iPhone sales."
    )
    sentiment: Optional[float] = Field(
        default=None,
        description="The sentiment score of the article, typically between -1 (negative) and 1 (positive)",
        example=0.85
    )
    link: Optional[str] = Field(
        default=None,
        description="The URL link to the full news article",
        example="https://example.com/news/apple-earnings-report"
    )
    source: Optional[str] = Field(
        default=None,
        description="The source of the news article",
        example="Bloomberg"
    )
    publication_date: Optional[datetime] = Field(
        default=None,
        description="The publication date and time of the news article",
        example="2024-09-02T15:45:00Z"
    )
    company_name: Optional[str] = Field(
        default=None,
        description="The name of the company mentioned in the article",
        example="Apple Inc."
    )
    company_link: Optional[str] = Field(
        default=None,
        description="The URL link to the company's profile or related page",
        example="https://example.com/company/apple"
    )

class ArticleCollection(BaseModel):
    source: Optional[str] = Field(
        default=None,
        description='The origin source of the articles, e.g., a news website or agency.'
    )
    link: Optional[str] = Field(
        default=None,
        description='A URL link to the collection of articles.'
    )
    extraction_date: Optional[datetime] = Field(
        default=None,
        description='The date and time when the article list was extracted.'
    )
    articles: List[NewsArticle] = Field(
        default_factory=list,
        description="A list containing instances of NewsArticle, representing individual news articles."
    )

class Insider(BaseModel):
    name: Optional[str] = Field(
        default=None, 
        description="The name of the insider"
    )
    current_position: Optional[str] = Field(
        default=None, 
        description="The current position held by the insider"
    )
    current_company: Optional[str] = Field(
        default=None, 
        description="The current company where the insider works"
    )
    company_url: Optional[str] = Field(
        default=None, 
        description="The URL to the insider's current company profile"
    )
    net_worth: Optional[str] = Field(
        default="N/A", 
        description="The net worth of the insider"
    )
    known_holdings: Optional[dict] = Field(
        default_factory=dict,
        description="Dictionary of known stock holdings with company names as keys and dictionary of information as values"
    )
    age: Optional[str] = Field(
        default="N/A", 
        description="The age of the insider"
    )
    industries: Optional[List[str]] = Field(
        default_factory=list,
        description="List of industries the insider is involved in"
    )
    summary: Optional[str] = Field(
        default="N/A", 
        description="A brief summary about the insider"
    )
    active_positions: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Dictionary of active positions with company names as keys and positions as values"
    )
    former_positions: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Dictionary of former positions with company names as keys and positions as values"
    )
    trainings: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Dictionary of trainings with institutions as keys and degrees as values"
    )
    link: Optional[str] = Field(
        default="https://www.marketscreener.com/insider/",
        description="Marketscreener link from which information was gotten"
    )

class Company(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description='Name of the company',
        example='Walmart'
    )
    isin: Optional[str] = Field(
        default=None,
        description='International Securities Identification Number of the company',
        example='US9311421039'
    )
    ticker: Optional[str] = Field(
        default=None,
        description='Stock ticker symbol of the company',
        example='WMT'
    )
    industry: Optional[str] = Field(
        default=None,
        description='Industry in which the company operates',
        example='Retail'
    )
    sector: Optional[str] = Field(
        default=None,
        description='Sector of the company',
        example='Consumer Services'
    )
    country: Optional[str] = Field(
        default=None,
        description='Country where the company is based',
        example='United States'
    )
    executives: Optional[dict] = Field(
        default=None,
        description='Dictionary containing key executives of the company',
        example={'Manager': {'Brien Brown': {'href': '/insider/BRIEN-BROWN-A1P6X4/',
                             'positions': {'Chief Tech/Sci/R&D Officer': '2008-12-31'}},
             'Lyndon Taylor': {'href': '/insider/LYNDON-TAYLOR-A0AXSA/',
                               'positions': {'General Counsel': '2023-09-24'}}}}
    )
    profile: Optional[str] = Field(
        default=None,
        description='Short profile of the company',
        example='Walmart Inc. is an American multinational retail corporation that operates a chain of hypermarkets, discount department stores, and grocery stores.'
    )
    link: Optional[str] = Field(
        default=None,
        description='Link to the company page',
        example='https://www.walmart.com'
    )
