import requests
import time
import random
import string
import threading
import argparse
from concurrent.futures import ThreadPoolExecutor

def generate_random_url():
    """Generate a random URL to shorten"""
    random_path = ''.join(random.choice(string.ascii_lowercase) for _ in range(15))
    return f"https://example.com/{random_path}"

def shorten_url(base_url):
    """Send a request to shorten a URL"""
    long_url = generate_random_url()
    try:
        response = requests.post(
            f"{base_url}/shorten",
            json={"url": long_url},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()['short_code']
        return None
    except Exception as e:
        print(f"Error shortening URL: {e}")
        return None

def access_shortened_url(base_url, short_code):
    """Access a shortened URL"""
    try:
        response = requests.get(
            f"{base_url}/{short_code}",
            timeout=5,
            allow_redirects=False  # Just check the redirect works, don't follow it
        )
        return response.status_code in (301, 302)  # Should get a redirect status
    except Exception as e:
        print(f"Error accessing shortened URL: {e}")
        return False

def worker(base_url, stats):
    """Worker function for each thread"""
    # First create a short URL
    short_code = shorten_url(base_url)
    if short_code:
        stats['shorten_success'] += 1
        
        # Then try to access it
        if access_shortened_url(base_url, short_code):
            stats['access_success'] += 1
        else:
            stats['access_failure'] += 1
    else:
        stats['shorten_failure'] += 1

def run_stress_test(base_url, num_requests, concurrency):
    """Run a stress test against the URL shortener"""
    stats = {
        'shorten_success': 0,
        'shorten_failure': 0,
        'access_success': 0,
        'access_failure': 0
    }
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        for _ in range(num_requests):
            executor.submit(worker, base_url, stats)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n--- Stress Test Results ---")
    print(f"Base URL: {base_url}")
    print(f"Number of requests: {num_requests}")
    print(f"Concurrency level: {concurrency}")
    print(f"Total duration: {duration:.2f} seconds")
    print(f"Requests per second: {num_requests / duration:.2f}")
    
    print("\n--- Success/Failure ---")
    print(f"URL Shortening Success: {stats['shorten_success']}")
    print(f"URL Shortening Failure: {stats['shorten_failure']}")
    print(f"URL Access Success: {stats['access_success']}")
    print(f"URL Access Failure: {stats['access_failure']}")
    
    success_rate = (stats['shorten_success'] + stats['access_success']) / (2 * num_requests) * 100
    print(f"\nOverall Success Rate: {success_rate:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='URL Shortener Stress Test')
    parser.add_argument('--url', required=True, help='Base URL of the URL shortener service')
    parser.add_argument('--requests', type=int, default=100, help='Number of requests to make')
    parser.add_argument('--concurrency', type=int, default=10, help='Number of concurrent requests')
    
    args = parser.parse_args()
    
    print(f"Starting stress test against {args.url} with {args.requests} requests at {args.concurrency} concurrency...")
    run_stress_test(args.url, args.requests, args.concurrency)