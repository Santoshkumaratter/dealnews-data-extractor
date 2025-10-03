import os
import base64
import random
import hashlib
from urllib.parse import urlparse
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

class ProxyMiddleware:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        ]

        # Optional explicit proxy pool (comma or newline separated)
        raw_list = os.getenv("PROXY_LIST", "").strip()
        self.proxy_pool: List[str] = []
        if raw_list:
            for line in raw_list.replace("\r", "\n").split("\n"):
                line = line.strip().strip(',')
                if not line:
                    continue
                if not line.startswith("http://") and not line.startswith("https://"):
                    line = f"http://{line}"
                self.proxy_pool.append(line)

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_request(self, request, spider):
        # Rotate UA on every request
        request.headers['User-Agent'] = random.choice(self.user_agents)
        
        # Set comprehensive browser-like headers to avoid detection
        request.headers.setdefault('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7')
        request.headers.setdefault('Accept-Language', 'en-US,en;q=0.9')
        request.headers.setdefault('Accept-Encoding', 'gzip, deflate, br')
        request.headers.setdefault('Connection', 'keep-alive')
        request.headers.setdefault('Upgrade-Insecure-Requests', '1')
        request.headers.setdefault('Sec-Fetch-Dest', 'document')
        request.headers.setdefault('Sec-Fetch-Mode', 'navigate')
        request.headers.setdefault('Sec-Fetch-Site', 'none')
        request.headers.setdefault('Sec-Fetch-User', '?1')
        request.headers.setdefault('Cache-Control', 'max-age=0')
        request.headers.setdefault('DNT', '1')
        
        # Add some randomization to avoid pattern detection
        if random.random() < 0.3:  # 30% chance to add extra headers
            request.headers.setdefault('Sec-Ch-Ua', '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"')
            request.headers.setdefault('Sec-Ch-Ua-Mobile', '?0')
            request.headers.setdefault('Sec-Ch-Ua-Platform', '"Windows"')

        # Check if proxy should be disabled (for local testing)
        if os.getenv('DISABLE_PROXY', 'true').lower() in ('1', 'true', 'yes'):
            spider.logger.debug("Proxy disabled for local testing")
            return None
            
        # Skip robots.txt requests to avoid proxy auth issues
        if 'robots.txt' in request.url:
            spider.logger.debug(f"Skipping robots.txt request: {request.url}")
            return None
            
        # Proxy selection
        self._apply_proxy(request, spider)

    def process_exception(self, request, exception, spider):
        # On network errors/timeouts: rotate UA and proxy, then retry
        spider.logger.warning(f"Request exception: {type(exception).__name__} for {request.url}; rotating proxy/UA and retrying")
        request.headers['User-Agent'] = random.choice(self.user_agents)
        self._apply_proxy(request, spider, force_rotate=True)
        request.dont_filter = True
        return request

    def process_response(self, request, response, spider):
        # Handle various HTTP errors
        if response.status == 429:
            spider.logger.info(f"Received 429 for {request.url}. Rotating proxy and retrying.")
            self._apply_proxy(request, spider, force_rotate=True)
            request.dont_filter = True
            return request
        elif response.status == 403:
            spider.logger.warning(f"Received 403 for {request.url}. Rotating UA and headers.")
            # Rotate user agent
            request.headers['User-Agent'] = random.choice(self.user_agents)
            # Add additional headers that might help bypass blocks
            request.headers.setdefault('Referer', 'https://www.google.com/')
            request.headers.setdefault('X-Forwarded-For', f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}")
            request.dont_filter = True
            return request
        elif response.status == 404:
            spider.logger.warning(f"Received 404 for {request.url}. Skipping this URL.")
            # Don't retry 404 errors, just log and continue
            return response
        elif response.status == 503:
            spider.logger.warning(f"Received 503 for {request.url}. Server overloaded, retrying with delay.")
            request.dont_filter = True
            return request
        return response

    def _apply_proxy(self, request, spider, force_rotate: bool = False):
        proxy_user = os.getenv("PROXY_USER")
        proxy_pass = os.getenv("PROXY_PASS")
        proxy_auth_header: Optional[str] = None

        # Debug proxy configuration
        if not proxy_user or not proxy_pass:
            spider.logger.warning("Proxy credentials not found - running without proxy")
            return

        # Prefer explicit proxy pool if provided
        if self.proxy_pool:
            proxy = random.choice(self.proxy_pool)
            spider.logger.debug(f"Using proxy from pool: {proxy}")
        else:
            # Webshare rotating gateway
            proxy_host = os.getenv("PROXY_HOST", "p.webshare.io")
            proxy_port = os.getenv("PROXY_PORT", "80")
            proxy = f"http://{proxy_host}:{proxy_port}"

        if proxy_user and proxy_pass:
            # For Webshare proxy, use the credentials in the URL
            proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

        prior_proxy = request.meta.get('proxy')
        if force_rotate or prior_proxy != proxy:
            request.meta['proxy'] = proxy
            spider.logger.info(f"Using proxy {proxy}")
