from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import requests, re
import MySQLdb.cursors
from transformers import pipeline
from newspaper import Article
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize the summarization pipeline
summarizer = pipeline('summarization', model='facebook/bart-large-cnn', revision='main')

# List of friendly news sources (example sources, replace with your actual list)
friendly_sources = [
    'bbc-news',
    'cnn',
    'the-verge',
    'techcrunch',
    # Add other sources you have identified
]

#MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'app_users'

mysql = MySQL(app)

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method=='POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            message = 'Logged in successfully'
            return redirect(url_for('home'), message=message)
        else:
            return render_template('login.html', error='Invalid username or password.')
    else:
        return render_template('login.html')
    
    # email = request[email]
    # password = request.form[password]

    # if not email or not password:
    #     return render_template('login.html', message='Please enter your email and password.')
    # else:
    #     #come back to this
    #     return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    message = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO users(username, password) VALUES (%s, %s)', (username, password))
        # mysql.connection.commit()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username, ))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return render_template('register.html', error='Invalid email address')
        elif not re.match(r'[A-Za-z0-9]+', username):
            # return render_template('register.html', error='Username must contain only characters and numbers')
            message = 'Username must contain only characters and numbers'
        elif not username or not password or not email:
            message = 'Please fill out the form'
        else:
            cursor.execuute('INSERT INTO users(username, password, email) VALUES (%s, %s, %s)', (username, hashed_password, email))
            mysql.connection.commit()
            message='You have successfully registered your account.'
    elif request.method == 'POST':
        message = 'Please fill out form.'
    return render_template('register.html', message=message)

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
        
    # # Render the template with the articles
    # if 'username' in sessions:
    #     return render_template('home.html', username=session['username'], articles=articles, search_query=search_query, weather=weather_info)
    # else:
    #     return render_template('home.html', articles=articles, search_query=search_query, weather=weather_info)
    
    return render_template('home.html', articles=articles, search_query=search_query, weather=weather_info)


@app.route('/save_article', methods=['POST'])
def save_article():
    article = request.form.to_dict()
    if 'saved_articles' not in session:
        session['saved_articles'] = []
    session['saved_articles'].append(article)
    session.modified = True
    return redirect(url_for('home'))

@app.route('/saved_articles')
def saved_articles():
    saved_articles = session.get('saved_articles', [])
    return render_template('saved_articles.html', articles=saved_articles)

if __name__ == '__main__':
    app.run(debug=True)
