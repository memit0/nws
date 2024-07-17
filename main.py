import requests
from transformers import pipeline
import os

api_key = os.getenv('NEWS_API_KEY')

# Initialize the summarization pipeline
summarizer = pipeline('summarization')

if not api_key:
    raise ValueError("No API key found. Please set the NEWS_API_KEY environment variable.")


# URL for the top headlines endpoint
url = 'https://newsapi.org/v2/top-headlines'

# Parameters for the request
params = {
    'country': 'us',  # You can change this to your preferred country
    'apiKey': api_key
}

# Making the request to the API
response = requests.get(url, params=params)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    # Print the headlines
    for article in data['articles']:
        title = article['title']
        description = article['description']
        url = article['url']
        
        # Print the title and URL
        print(f"Title: {title}")
        print(f"URL: {url}")
        
        if description:
            # Summarize the description
            summary = summarizer(description, max_length=50, min_length=25, do_sample=False)
            # Print the original description and its summary
            print(f"Description: {description}")
            print(f"Summary Description: {summary[0]['summary_text']}")
        else:
            print("Description: No description provided.")
        
        print('-' * 40)
else:
    print(f"Failed to fetch news: {response.status_code}")
