from flask import Flask, render_template, jsonify, logging, request, session, redirect, url_for
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
# from models import User, db
import requests, re
import MySQLdb.cursors
from transformers import pipeline
from newspaper import Article
import os

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'your_secret_key'

# Configure your Flask app
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///flaskdb.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')  # Ensure this key is strong and secure

# Enable CORS for requests including credentials
CORS(app, supports_credentials=True)

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
# Initialize the summarization pipeline
summarizer = pipeline('summarization', model='facebook/bart-large-cnn', revision='main')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Example, update as needed
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)

with app.app_context():
    db.create_all()
class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)


# List of friendly news sources (example sources, replace with your actual list)
friendly_sources = [
    'bbc-news',
    'cnn',
    'the-verge',
    'techcrunch',
    # Add other sources you have identified
]


# Check if user is logged in
# @app.route('/check_session', methods=['GET'])
# def check_session():
#     if 'user_id' in session:
#         return jsonify({'status': 'logged in'})
#     return jsonify({'status': 'not logged in'})

@app.route('/login', methods=['POST','GET'])
def login():
    message=''
    if request.method == 'POST':
        username_input = request.form.get('username')
        password_input = request.form.get('password')

        # account = user.query.filter_by(username=username).first()
        account = user.query.filter_by(username=username_input).first()
        # password = user.query.filter_by(Password=request.form['password']).first()

        if account and bcrypt.check_password_hash(account.password, password_input):
            session['logged_in'] = True
            session['user_id'] = account.id
            # return render_template('login.html', success='Login successful.')
            return redirect(url_for('saved_articles', success='Login successful.'))
        else:
            return render_template('login.html', error='Invalid username or password.')
        
        # session['user_id'] = user.id

    return render_template('login.html', success='Login successful.')

    # email = request[email]
    # password = request.form[password]

    # if not email or not password:
    #     return render_template('login.html', message='Please enter your email and password.')
    # else:
    #     #come back to this
    #     return render_template('login.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    message=''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        username= request.form.get('username')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        
        account = user.query.filter_by(email=email).first()
        if account:
            return render_template('register.html', message='Account already exists.') 
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return render_template('register.html', error='Invalid email address.')   
        elif not re.match(r'[A-Za-z0-9]+', username):
            return render_template('register.html', error='Username must contain only characters and numbers.')
        elif not email or not password or not username:
            return render_template('register.html', error = 'Please enter all required fields.')
        
        new_user = user(email=email, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        # session['user_id'] = new_user.id
        return redirect(url_for('login', regsuccess='Account created successfully. Please log in.'))

    return render_template('register.html')


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
def save_article(user_id):
    article = request.form.to_dict()
    if 'saved_articles' not in session:
        session['saved_articles'] = []
    session['saved_articles'].append(article)
    session.modified = True
    return redirect(url_for('home'))

@app.route('/saved_articles')
def saved_articles():
    if 'logged_in' in session and session['logged_in']:
        # Fetch saved articles and render the template
        articles = save_article(session['user_id'])
        return render_template('saved_articles.html', articles=articles)
    else:
        return render_template('login.html', error='You must be logged in to view saved articles.')
    
    # saved_articles = session.get('saved_articles', [])
    # return render_template('saved_articles.html', articles=saved_articles)

if __name__ == '__main__':
    # db.create_all()
    app.run(debug=True)
