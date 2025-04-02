import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

class URLShortenerTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        """Test that the home page loads correctly"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'URL Shortener', response.data)

    def test_shorten_url(self):
        """Test that the API properly shortens URLs"""
        test_url = "https://www.example.com/some/very/long/url/that/needs/shortening"
        response = self.app.post('/api/shorten', 
                                json={'url': test_url},
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('short_url', data)
        self.assertIn('original_url', data)
        self.assertEqual(data['original_url'], test_url)
        
        # Verify short URL format
        short_code = data['short_url'].split('/')[-1]
        self.assertTrue(len(short_code) > 0)
        
    def test_invalid_url(self):
        """Test that invalid URLs are properly rejected"""
        invalid_url = "not-a-valid-url"
        response = self.app.post('/api/shorten', 
                                json={'url': invalid_url},
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_missing_url(self):
        """Test that requests without URLs are properly rejected"""
        response = self.app.post('/api/shorten', 
                                json={},
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('app.redis_client')
    def test_redirect(self, mock_redis):
        """Test that short URLs redirect to the original URL"""
        # Mock the Redis client to return a known URL
        original_url = "https://www.example.com/original"
        short_code = "abc123"
        mock_redis.get.return_value = original_url.encode('utf-8')
        
        response = self.app.get(f'/{short_code}')
        
        # Check that Redis was called with the right key
        mock_redis.get.assert_called_once_with(short_code)
        
        # Check that we get redirected to the right place
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, original_url)

    @patch('app.redis_client')
    def test_nonexistent_short_url(self, mock_redis):
        """Test handling of nonexistent short URLs"""
        # Mock Redis to return None for a nonexistent key
        mock_redis.get.return_value = None
        
        response = self.app.get('/nonexistent')
        
        self.assertEqual(response.status_code, 404)

    @patch('app.generate_short_code')
    @patch('app.redis_client')
    def test_collision_handling(self, mock_redis, mock_generate_code):
        """Test that URL code collisions are handled properly"""
        # First call to generate_short_code returns a code that already exists
        # Second call returns a unique code
        mock_generate_code.side_effect = ["existing", "unique"]
        
        # Mock redis.get to return a value for "existing" and None for "unique"
        def mock_get(key):
            if key == "existing":
                return b"https://www.example.com/already-exists"
            return None
        
        mock_redis.get.side_effect = mock_get
        mock_redis.set = MagicMock()
        
        test_url = "https://www.example.com/new-url"
        with patch('app.redis_client.get', side_effect=mock_get):
            response = self.app.post('/api/shorten', 
                                    json={'url': test_url},
                                    content_type='application/json')
        
        # Should have called generate_short_code twice
        self.assertEqual(mock_generate_code.call_count, 2)
        
        # Should have set the new URL with the unique code
        mock_redis.set.assert_called_with("unique", test_url)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("unique", data["short_url"])

if __name__ == '__main__':
    unittest.main()