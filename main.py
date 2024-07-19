from flask import Flask, render_template
import requests
from transformers import pipeline
import os

# Initialize the summarization pipeline
summarizer = pipeline('summarization', model='facebook/bart-large-cnn', revision='main')

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

    # Fetch Weather Data
    api_key_weather = os.getenv('WEATHER_API_KEY')
    if not api_key_weather:
        raise ValueError("No WEATHER_API_KEY found. Please set the WEATHER_API_KEY environment variable.")

    weather_url = 'https://api.weatherbit.io/v2.0/current'
    weather_params = {'city': 'New York', 'country': 'US', 'key': api_key_weather}
    weather_response = requests.get(weather_url, params=weather_params)

    if weather_response.status_code == 200:
        weather_data = weather_response.json()
        weather = weather_data['data'][0]
        weather_info = {
            'city_name': weather['city_name'],
            'temp': weather['temp'],
            'weather_description': weather['weather']['description']
        }
    else:
        weather_info = None
        
    # Render the template with the articles
    return render_template('home.html', articles=articles, weather=weather_info)





if __name__ == '__main__':
    app.run(debug=True)
