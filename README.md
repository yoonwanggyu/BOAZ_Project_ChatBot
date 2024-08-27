### `CrawlingCard.py` Script

This script crawls the [Card Gorilla](https://www.card-gorilla.com/home) website to extract and save card information for 10 different card companies.

#### Features:
- **Data Extraction**: Scrapes card data for 10 card companies.
- **Ad Handling**: Manages pop-up ads during the crawling process to ensure smooth operation.
- **Organized Output**: Saves each company's card information in a separate, well-structured JSON file.

#### Example Output File
Each output file is named after the card company and contains details of the top 10 cards offered by that company. The structure of the JSON file is as follows:

```json
{
    "card_company": "Samsung Card",
    "cards": [
        {
            "name": "Samsung Card & MILEAGE PLATINUM (SkyPass)",
            "summary": "Earn miles, enjoy dining discounts, and more.",
            "benefits": {
                "Mileage": ["1.5 miles per $1 spent on airlines"],
                "Dining": ["10% discount at partner restaurants"],
                ...
            }
        },
        {
            "name": "Samsung Card 2",
            "summary": "Various benefits tailored for lifestyle and shopping.",
            "benefits": {
                "Shopping": ["5% discount at select stores"],
                "Travel": ["Access to airport lounges"],
                ...
            }
        },
        ...
    ]
}
```

Each JSON file includes:
- **card_company**: The name of the card company.
- **cards**: A list of the top 10 cards, each with:
  - **name**: The card's name.
  - **summary**: A brief overview of the card's key features.
  - **benefits**: A dictionary containing the specific benefits of the card. Each key represents a category of benefits, and the associated list contains details of the benefits within that category.
