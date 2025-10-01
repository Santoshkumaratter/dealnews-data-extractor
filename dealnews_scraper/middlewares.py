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
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
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
        request.headers.setdefault('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        request.headers.setdefault('Accept-Language', 'en-US,en;q=0.9')

        # Check if proxy should be disabled (for local testing)
        if os.getenv('DISABLE_PROXY', '').lower() in ('1', 'true', 'yes'):
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
        # Handle 429 Too Many Requests by rotating proxy and retrying
        if response.status == 429:
            spider.logger.info(f"Received 429 for {request.url}. Rotating proxy and retrying.")
            self._apply_proxy(request, spider, force_rotate=True)
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
