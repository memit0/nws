from flask import Flask, render_template
import requests
from transformers import pipeline
import os

# Initialize the summarization pipeline
summarizer = pipeline('summarization')

app = Flask(__name__)

@app.route('/')
def home():
    api_key = os.getenv('NEWS_API_KEY')

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

    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        articles = []

        # Collect articles with summaries
        for article in data['articles']:
            title = article['title']
            description = article['description']
            url = article['url']
            
            if description:
                # Summarize the description
                summary = summarizer(description, max_length=50, min_length=25, do_sample=False)
                summary_text = summary[0]['summary_text']
            else:
                summary_text = "No description provided."
            
            articles.append({
                'title': title,
                'summary': summary_text,
                'url': url
            })
        
        # Render the template with the articles
        return render_template('home.html', articles=articles)
    else:
        return f"Failed to fetch news: {response.status_code}", 500

if __name__ == '__main__':
    app.run(debug=True)
