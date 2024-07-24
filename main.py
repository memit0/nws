from flask import Flask, render_template, request, session, redirect, url_for
import requests
from transformers import pipeline
from newspaper import Article
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize the summarization pipeline
summarizer = pipeline('summarization')

# List of friendly news sources (example sources, replace with your actual list)
friendly_sources = [
    'bbc-news',
    'cnn',
    'the-verge',
    'techcrunch',
    # Add other sources you have identified
]

# Function to scrape full text and meta description of an article using newspaper3k
def scrape_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        if not article.is_parsed:
            print(f"Failed to parse article from URL: {url}")
            return None, None
        return article.text, article.meta_description
    except Exception as e:
        print(f"Error scraping article from URL: {url}")
        print(f"Exception: {e}")
        return None, None

@app.route('/', methods=['GET', 'POST'])
def home():
    print("Entered home route")  # Debug statement
    api_key_news = os.getenv('NEWS_API_KEY')
    if not api_key_news:
        raise ValueError("No NEWS_API_KEY found. Please set the NEWS_API_KEY environment variable.")

    search_query = request.form.get('search_query')
    news_url = 'https://newsapi.org/v2/everything' if search_query else 'https://newsapi.org/v2/top-headlines'
    news_params = {
        'q': search_query,
        'sources': ','.join(friendly_sources),  # Filter by friendly sources
        'apiKey': api_key_news
    }
    news_response = requests.get(news_url, params=news_params)
    print(f"News API response status code: {news_response.status_code}")  # Debug statement

    articles = []
    if news_response.status_code == 200:
        news_data = news_response.json()
        print(f"News data received: {news_data}")  # Debug statement
        for article in news_data['articles']:
            title = article['title']
            url = article['url']
            print(f"Processing article: {title}, {url}")  # Debug statement
            full_text, meta_description = scrape_article_text(url)
            print(f"Full text scraped: {full_text[:100]}...")  # Debug statement

            if full_text:
                try:
                    # Ensure full_text is long enough for summarization
                    if len(full_text.split()) > 50:  # Check if text has more than 50 words
                        summary = summarizer(full_text, max_length=150, min_length=50, do_sample=False)
                        summary_text = summary[0]['summary_text']
                        print(f"Summary: {summary_text}")  # Debug statement
                    else:
                        summary_text = full_text  # Use full_text instead of summary
                        print("Text too short to summarize, using full text.")  # Debug statement
                except Exception as e:
                    # Skip articles that cause summarization errors
                    print(f"Skipping article due to summarization error: {e}")
                    continue  # Skip this article and proceed with the next one
            else:
                summary_text = meta_description or "No description available."

            articles.append({'title': title, 'summary': summary_text, 'url': url})
    else:
        print(f"Error fetching news articles: {news_response.text}")  # Debug statement

    print(f"Articles to display: {articles}")  # Debug statement


    # Fetch Weather Data
    api_key_weather = os.getenv('WEATHER_API_KEY')
    if not api_key_weather:
        raise ValueError("No WEATHER_API_KEY found. Please set the WEATHER_API_KEY environment variable.")
    
    weather_url = 'https://api.weatherbit.io/v2.0/current'
    weather_params = {'city': 'New York', 'country': 'US', 'key': api_key_weather, 'units': 'I'}
    weather_response = requests.get(weather_url, params=weather_params)

    if weather_response.status_code == 200:
        weather_data = weather_response.json()
        weather = weather_data['data'][0]
        weather_info = {
            'city_name': weather['city_name'],
            'temp': round(weather['temp']),
            'weather_description': weather['weather']['description']
        }
    else:
        weather_info = None

    return render_template('home.html', articles=articles, search_query=search_query, weather=weather_info)

@app.route('/save_article', methods=['POST'])
def save_article():
    article = request.get_json()
    if 'saved_articles' not in session:
        session['saved_articles'] = []
    session['saved_articles'].append(article)
    session.modified = True
    return '', 204

@app.route('/saved_articles')
def saved_articles():
    saved_articles = session.get('saved_articles', [])
    
    # Fetch Weather Data
    api_key_weather = os.getenv('WEATHER_API_KEY')
    if not api_key_weather:
        raise ValueError("No WEATHER_API_KEY found. Please set the WEATHER_API_KEY environment variable.")
    
    weather_url = 'https://api.weatherbit.io/v2.0/current'
    weather_params = {'city': 'New York', 'country': 'US', 'key': api_key_weather, 'units': 'I'}
    weather_response = requests.get(weather_url, params=weather_params)

    if weather_response.status_code == 200:
        weather_data = weather_response.json()
        weather = weather_data['data'][0]
        weather_info = {
            'city_name': weather['city_name'],
            'temp': round(weather['temp']),
            'weather_description': weather['weather']['description']
        }
    else:
        weather_info = None

    return render_template('saved_articles.html', articles=saved_articles, weather=weather_info)


if __name__ == '__main__':
    app.run(debug=True)

