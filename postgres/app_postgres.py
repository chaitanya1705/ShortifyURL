import os
import random
import string
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from flask import Flask, request, redirect, jsonify, render_template

app = Flask(__name__)

# PostgreSQL Connection Pool
db_params = {
    "dbname": os.environ.get("DB_NAME", "urlshortener"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
}

# Create a connection pool
connection_pool = SimpleConnectionPool(1, 10, **db_params)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    connection = connection_pool.getconn()
    try:
        yield connection
    finally:
        connection_pool.putconn(connection)

def init_db():
    """Initialize the database with the URLs table"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id SERIAL PRIMARY KEY,
                    short_code VARCHAR(10) UNIQUE,
                    long_url TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            """)
        conn.commit()

# Configuration
base_url = os.environ.get('BASE_URL', 'http://localhost:5000')
shortcode_length = int(os.environ.get('SHORTCODE_LENGTH', 6))

def generate_short_code():
    """Generate a random short code for URLs"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(shortcode_length))

@app.route('/')
def index():
    """Render the home page with a form to shorten URLs"""
    return render_template('index.html', base_url=base_url)

@app.route('/shorten', methods=['POST'])
def shorten_url():
    """API endpoint to shorten a URL"""
    data = request.get_json()
    if not data or not data.get('url'):
        return jsonify({'error': 'No URL provided'}), 400
    
    long_url = data['url']
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if URL already exists
            cur.execute("SELECT short_code FROM urls WHERE long_url = %s", (long_url,))
            result = cur.fetchone()
            
            if result:
                short_code = result[0]
            else:
                # Create new short code
                short_code = generate_short_code()
                while True:
                    cur.execute("SELECT 1 FROM urls WHERE short_code = %s", (short_code,))
                    if not cur.fetchone():
                        break
                    short_code = generate_short_code()
                
                cur.execute(
                    "INSERT INTO urls (short_code, long_url) VALUES (%s, %s)",
                    (short_code, long_url)
                )
                conn.commit()
    
    return jsonify({
        'short_url': f"{base_url}/{short_code}",
        'long_url': long_url,
        'short_code': short_code
    })

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirect from a short URL to the original URL"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT long_url FROM urls WHERE short_code = %s", (short_code,))
            result = cur.fetchone()
            
            if result:
                long_url = result[0]
                # Update access count
                cur.execute("UPDATE urls SET access_count = access_count + 1 WHERE short_code = %s", (short_code,))
                conn.commit()
                return redirect(long_url)
    
    return jsonify({'error': 'URL not found'}), 404

@app.route('/stats')
def stats():
    """Return statistics about the URL shortener"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM urls")
            total_urls = cur.fetchone()[0]
            
            cur.execute("SELECT SUM(access_count) FROM urls")
            total_clicks = cur.fetchone()[0] or 0
            
            cur.execute("""
                SELECT short_code, long_url, access_count 
                FROM urls 
                ORDER BY access_count DESC 
                LIMIT 5
            """)
            top_urls = [{
                'short_code': row[0],
                'long_url': row[1],
                'access_count': row[2]
            } for row in cur.fetchall()]
    
    return jsonify({
        'total_urls': total_urls,
        'total_clicks': total_clicks,
        'top_urls': top_urls,
        'instance_id': os.environ.get('HOSTNAME', 'local')
    })

# Initialize database on startup
@app.before_first_request
def before_first_request():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)