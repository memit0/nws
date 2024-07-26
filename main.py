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

# Mock data for business articles
business_articles = [
    {
        'title': 'Amazon Q2 Earnings Exceed Expectations, Stock Soars',
        'summary': 'Amazon reported second-quarter earnings that exceeded analysts’ expectations, driven by strong sales in its cloud computing and e-commerce divisions. The company’s stock surged by 8% in after-hours trading as investors reacted positively to the news.',
        'url': 'https://example.com/amazon-q2-earnings'
    },
    {
        'title': 'Tesla Announces New Model Y Variants Amid Growing Demand',
        'summary': 'Tesla has unveiled new variants of its popular Model Y electric SUV, including a longer-range version and a performance-oriented model. The announcement comes amid growing global demand for electric vehicles and is expected to further boost Tesla’s market share.',
        'url': 'https://example.com/tesla-new-model-y'
    },
    {
        'title': 'Apple to Invest $1 Billion in New Silicon Valley Campus',
        'summary': 'Apple Inc. announced plans to invest $1 billion in the construction of a new campus in Silicon Valley. The new facility will serve as a hub for research and development and is expected to create thousands of jobs in the region.',
        'url': 'https://example.com/apple-new-campus'
    },
    {
        'title': 'Google’s AI Division Launches New Suite of Tools for Developers',
        'summary': 'Google’s AI division has launched a new suite of tools aimed at helping developers integrate artificial intelligence into their applications. The tools, which include advanced machine learning algorithms and easy-to-use APIs, are designed to accelerate innovation and enhance the capabilities of software applications.',
        'url': 'https://example.com/google-ai-tools'
    },
    {
        'title': 'Microsoft Teams Surpasses 300 Million Monthly Active Users',
        'summary': 'Microsoft Teams has surpassed 300 million monthly active users, cementing its position as a leading collaboration platform for businesses. The milestone highlights the growing adoption of remote work tools and Microsoft’s continued dominance in the enterprise software market.',
        'url': 'https://example.com/microsoft-teams-300-million'
    }
]

entertainment_articles = [
    {
        'title': 'Oscars 2024: Major Wins and Surprises of the Night',
        'summary': 'The 2024 Oscars were filled with surprising wins and heartfelt speeches. Major awards went to unexpected recipients, making the night one to remember.',
        'url': 'https://example.com/oscars-2024-wins'
    },
    {
        'title': 'New Marvel Movie Breaks Box Office Records',
        'summary': 'The latest Marvel movie has shattered box office records, becoming the highest-grossing film of the year within its first weekend.',
        'url': 'https://example.com/marvel-box-office'
    },
    {
        'title': 'Grammy Awards 2024: Best Performances and Winners',
        'summary': 'The 2024 Grammy Awards featured unforgettable performances and notable wins. Artists from various genres were celebrated for their musical achievements.',
        'url': 'https://example.com/grammys-2024'
    },
    {
        'title': 'Celebrity Couple Announces Engagement',
        'summary': 'A famous celebrity couple has announced their engagement, sending fans into a frenzy. The announcement was made through a heartfelt social media post.',
        'url': 'https://example.com/celebrity-engagement'
    },
    {
        'title': 'New Netflix Series Gains Popularity',
        'summary': 'A new Netflix series has quickly gained popularity among viewers, praised for its gripping storyline and outstanding performances.',
        'url': 'https://example.com/netflix-series'
    },
    {
        'title': 'Film Festival 2024: Highlights and Award Winners',
        'summary': 'The 2024 Film Festival showcased an array of incredible films from around the world. Highlights include award-winning films and groundbreaking performances.',
        'url': 'https://example.com/film-festival-2024'
    }
]

politics_articles = [
    {
        'title': 'New Policy Reforms Announced by the Government',
        'summary': 'The government has announced a series of new policy reforms aimed at improving economic growth and social welfare. These reforms are expected to bring significant changes in the coming years.',
        'url': 'https://example.com/new-policy-reforms'
    },
    {
        'title': 'Elections 2024: Key Candidates and Issues',
        'summary': 'The upcoming 2024 elections are drawing attention, with key candidates outlining their platforms and major issues being debated by the public.',
        'url': 'https://example.com/elections-2024'
    },
    {
        'title': 'International Summit Focuses on Climate Change',
        'summary': 'World leaders have gathered for an international summit focusing on climate change, discussing strategies to combat global warming and promote sustainability.',
        'url': 'https://example.com/climate-summit'
    },
    {
        'title': 'New Trade Agreement Signed Between Countries',
        'summary': 'A new trade agreement has been signed between several countries, aimed at boosting economic cooperation and reducing trade barriers.',
        'url': 'https://example.com/trade-agreement'
    },
    {
        'title': 'Government Faces Challenges in Implementing New Policies',
        'summary': 'The government is facing significant challenges in implementing new policies, with opposition parties and public opinion posing obstacles.',
        'url': 'https://example.com/policy-challenges'
    },
    {
        'title': 'Political Scandal Unfolds as Investigation Continues',
        'summary': 'A major political scandal is unfolding as investigations continue, revealing corruption and misconduct among high-ranking officials.',
        'url': 'https://example.com/political-scandal'
    }
]

health_articles = [
    {
        'title': 'Breakthrough in Cancer Research: New Treatment Shows Promise',
        'summary': 'Scientists have made a breakthrough in cancer research with a new treatment that has shown promising results in early trials. This could be a significant step forward in the fight against cancer.',
        'url': 'https://example.com/cancer-research-breakthrough'
    },
    {
        'title': 'Health Benefits of a Mediterranean Diet',
        'summary': 'Recent studies have highlighted the numerous health benefits of a Mediterranean diet, including reduced risk of heart disease and improved cognitive function.',
        'url': 'https://example.com/mediterranean-diet'
    },
    {
        'title': 'New Advances in Mental Health Treatment',
        'summary': 'Researchers have developed new advances in mental health treatment, offering hope for more effective therapies for conditions such as depression and anxiety.',
        'url': 'https://example.com/mental-health-advances'
    },
    {
        'title': 'Public Health Campaign Promotes Vaccination',
        'summary': 'A new public health campaign is promoting vaccination to prevent the spread of infectious diseases, emphasizing the importance of immunization for community health.',
        'url': 'https://example.com/vaccination-campaign'
    },
    {
        'title': 'Study Finds Link Between Exercise and Longevity',
        'summary': 'A recent study has found a strong link between regular exercise and increased longevity, suggesting that physical activity can significantly extend life expectancy.',
        'url': 'https://example.com/exercise-longevity'
    },
    {
        'title': 'Innovative Telehealth Services Expand Access to Care',
        'summary': 'Innovative telehealth services are expanding access to healthcare, allowing patients to receive medical consultations and treatment remotely.',
        'url': 'https://example.com/telehealth-services'
    }
]


@app.route('/business', methods=['GET'])
def business():
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

    return render_template('business.html', articles=business_articles, weather=weather_info)

@app.route('/entertainment', methods=['GET'])
def entertainment():
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

    return render_template('entertainment.html', articles=entertainment_articles, weather=weather_info)

@app.route('/politics', methods=['GET'])
def politics():
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

    return render_template('politics.html', articles=politics_articles, weather=weather_info)

@app.route('/health', methods=['GET'])
def health():
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

    return render_template('health.html', articles=health_articles, weather=weather_info)





@app.route('/', methods=['GET', 'POST'])
def home():
    print("Entered home route")  # Debug statement
    api_key_news = os.getenv('NEWS_API_KEY')
    if not api_key_news:
        raise ValueError("No NEWS_API_KEY found. Please set the NEWS_API_KEY environment variable.")

    search_query = request.form.get('search_query')
    news_url = 'https://newsapi.org/v2/top-headlines' if not search_query else 'https://newsapi.org/v2/everything'
    news_params = {
        'apiKey': api_key_news,
        'sources': ','.join(friendly_sources) if not search_query else '',
        'q': search_query if search_query else '',
        'language': 'en'
    }
    news_response = requests.get(news_url, params=news_params)
    print(f"News API response status code: {news_response.status_code}")  # Debug statement

    articles = []
    if news_response.status_code == 200:
        news_data = news_response.json()
        print(f"News data received: {news_data}")  # Debug statement
        if 'articles' in news_data:
            for article in news_data['articles']:
                title = article.get('title')
                url = article.get('url')
                print(f"Processing article: {title}, {url}")  # Debug statement
                full_text, meta_description = scrape_article_text(url)
                if full_text:
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
                    print("Full text or meta description not found for this article.")  # Debug statement
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
        if 'data' in weather_data and len(weather_data['data']) > 0:
            weather = weather_data['data'][0]
            weather_info = {
                'city_name': weather['city_name'],
                'temp': round(weather['temp']),
                'weather_description': weather['weather']['description']
            }
        else:
            weather_info = None
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

@app.route('/remove_article', methods=['POST'])
def remove_article():
    article_data = request.get_json()
    saved_articles = session.get('saved_articles', [])

    # Find the article to remove
    for article in saved_articles:
        if article['title'] == article_data['title'] and article['url'] == article_data['url']:
            saved_articles.remove(article)
            break

    session['saved_articles'] = saved_articles
    session.modified = True
    return '', 204


if __name__ == '__main__':
    app.run(debug=True)
