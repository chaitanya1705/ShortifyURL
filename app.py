import os
import random
import string
import redis
from flask import Flask, request, redirect, jsonify, render_template

app = Flask(__name__)

# Connect to Redis
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)

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
    
    # Check if URL already has a short code
    for key in redis_client.keys('*'):
        if redis_client.get(key).decode('utf-8') == long_url:
            short_code = key.decode('utf-8')
            return jsonify({
                'short_url': f"{base_url}/{short_code}",
                'long_url': long_url,
                'short_code': short_code
            })
    
    # Create new short code
    short_code = generate_short_code()
    while redis_client.exists(short_code):
        short_code = generate_short_code()
    
    # Store in Redis
    redis_client.set(short_code, long_url)
    
    return jsonify({
        'short_url': f"{base_url}/{short_code}",
        'long_url': long_url,
        'short_code': short_code
    })

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirect from a short URL to the original URL"""
    long_url = redis_client.get(short_code)
    if long_url:
        return redirect(long_url.decode('utf-8'))
    return jsonify({'error': 'URL not found'}), 404

@app.route('/stats')
def stats():
    """Return statistics about the URL shortener"""
    total_urls = len(redis_client.keys('*'))
    return jsonify({
        'total_urls': total_urls,
        'instance_id': os.environ.get('HOSTNAME', 'local')
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)