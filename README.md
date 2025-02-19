# Argus: Real-Time Monitoring of Company-Specific News for Liquidity Events

![Argus Logo](argus_logo_2.png)

## Overview

Argus is a powerful tool designed to monitor company-specific news and identify potential liquidity events. By leveraging data from financial news sources, Argus provides insights into individuals who may have recently come into wealth or are poised to do so. This project aims to offer a real-time perspective on financial activities that could indicate significant economic changes for companies and their insiders.

## Objectives

- **Real-Time Monitoring**: Continuously track news articles and insider information to detect liquidity events such as IPOs, mergers, acquisitions, and funding rounds.
- **Data Analysis**: Analyze patterns and keywords in the data to identify potential wealth-generating events.
- **Alert System**: Notify users of detected events through various channels, ensuring timely awareness of significant financial activities.
- **Comprehensive Insights**: Provide a detailed view of the financial landscape, focusing on individuals and companies likely to experience economic shifts.

## Methodology

1. **Data Collection**:

   - Utilize web scraping techniques to gather data from MarketScreener, focusing on insider information, company details, and news articles.
   - Implement a scheduling mechanism to ensure data is collected at regular intervals for real-time analysis.
2. **Data Analysis**:

   - Develop algorithms to parse and analyze the collected data, identifying keywords and patterns indicative of liquidity events.
   - Use machine learning models to enhance the accuracy of event detection and prediction.
3. **Alert System**:

   - Set up an alert system to notify users of potential liquidity events via email, SMS, or a web dashboard.
   - Customize alert settings to cater to user preferences and priorities.
4. **Data Storage and Management**:

   - Store collected data in a structured database, enabling efficient querying and analysis.
   - Ensure data integrity and compliance with privacy regulations.
5. **User Interface**:

   - Develop a user-friendly interface to display insights and alerts, providing users with a comprehensive view of the financial landscape.

## Getting Started

To get started with Argus, follow these steps:

1. Clone the repository: `git clone {TO-DO}`
2. Install the required dependencies: `pip install -r requirements.txt`
3. Set up your database and configure the environment variables.
4. Run the data collection scripts to start monitoring news and insider information.
5. Access the dashboard to view insights and manage alerts.

## Contributing

We welcome contributions to Argus! If you're interested in contributing, please read our [contribution guidelines](CONTRIBUTING.md) and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or feedback, please contact [Alvin](mailto:alvin_leung@u.nus.edu).
