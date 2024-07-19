import os
from flask import Flask, jsonify, render_template, request
from transformers import pipeline
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the summarization pipeline
summarizer = pipeline('summarization', model='facebook/bart-large-cnn', revision='main')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your actual secret key

# Directly set the API key
api_key = 'your_api_key'  # Replace with your actual API key

@app.route('/')
def index():
    return render_template('index.html')  # No need for 'templates/' prefix

@app.route('/news', methods=['GET'])
def get_news():
    url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'country': 'us',
        'apiKey': api_key
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = []
        for article in data['articles']:
            title = article['title']
            description = article['description']
            article_url = article['url']
            if description:
                summary = summarizer(description, max_length=50, min_length=25, do_sample=False)
                articles.append({
                    'title': title,
                    'url': article_url,
                    'description': description,
                    'summary': summary[0]['summary_text']
                })
        return jsonify(articles)
    else:
        return jsonify({'error': f"Failed to fetch news: {response.status_code}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
