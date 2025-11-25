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
        # Runtime flags/counters
        self.disable_proxy_runtime = False
        self.consecutive_407_count = 0
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
        
        # If runtime fallback disabled proxy, skip applying proxy
        if self.disable_proxy_runtime:
            return None

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

        # Check if proxy should be disabled (for local testing) - default to enabled
        if os.getenv('DISABLE_PROXY', 'false').lower() in ('1', 'true', 'yes'):
            spider.logger.debug("Proxy disabled for local testing")
            return None
            
        # Skip robots.txt requests to avoid proxy auth issues
        if 'robots.txt' in request.url:
            spider.logger.debug(f"Skipping robots.txt request: {request.url}")
            return None
            
        # Proxy selection
        self._apply_proxy(request, spider)

    def process_exception(self, request, exception, spider):
        # On network errors/timeouts: rotate UA and proxy, then retry with delay
        exception_name = type(exception).__name__
        spider.logger.warning(f"Request exception: {exception_name} for {request.url}; rotating proxy/UA and retrying with delay")

        # If proxy auth failed (407), disable proxy for this request to avoid hard fail
        exc_text = str(exception)
        if 'Proxy Authentication Required' in exc_text or '407' in exc_text:
            spider.logger.error("Proxy authentication failed (407). Disabling proxy immediately for the rest of the run.")
            if 'proxy' in request.meta:
                request.meta.pop('proxy', None)
            # Disable proxy for the remainder of the run and clear auth header
            self.disable_proxy_runtime = True
            if 'Proxy-Authorization' in request.headers:
                try:
                    del request.headers['Proxy-Authorization']
                except Exception:
                    pass
            request.dont_filter = True
            return request

        # Rotate user agent
        request.headers['User-Agent'] = random.choice(self.user_agents)

        # Add extra delay for connection issues
        request.meta['download_delay'] = 10  # 10 second delay for retries

        # Apply proxy rotation
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
        elif response.status == 407:
            # Proxy authentication required
            spider.logger.error(f"Received 407 (Proxy Authentication Required) for {request.url}. Disabling proxy immediately for the rest of the run.")
            request.meta.pop('proxy', None)
            # Disable proxy for the remainder of the run and clear auth header
            self.disable_proxy_runtime = True
            if 'Proxy-Authorization' in request.headers:
                try:
                    del request.headers['Proxy-Authorization']
                except Exception:
                    pass
            request.dont_filter = True
            return request
        elif response.status == 403:
            # Track retry count for exponential backoff
            retry_count = request.meta.get('retry_403_count', 0)
            if retry_count >= 3:
                spider.logger.error(f"Received 403 for {request.url} after {retry_count} retries. Skipping.")
                return response  # Stop retrying after 3 attempts
            
            # Exponential backoff delay
            delay = (2 ** retry_count) * 5  # 5s, 10s, 20s
            spider.logger.warning(f"Received 403 for {request.url}. Retry {retry_count + 1}/3 with {delay}s delay. Rotating UA and headers.")
            
            # Rotate user agent
            request.headers['User-Agent'] = random.choice(self.user_agents)
            # Add additional headers that might help bypass blocks
            request.headers['Referer'] = 'https://www.google.com/'
            request.headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            
            # Set download delay for this request
            request.meta['download_delay'] = delay
            request.meta['retry_403_count'] = retry_count + 1
            request.dont_filter = True
            return request
        elif response.status == 404:
            spider.logger.warning(f"Received 404 for {request.url}. Skipping this URL.")
            # Don't retry 404 errors, just log and continue
            return response
        elif response.status == 400:
            # Bad request usually indicates invalid/overflown pagination; do not retry
            spider.logger.info(f"Received 400 for {request.url}. Not retrying this URL.")
            return response
        elif response.status == 503:
            spider.logger.warning(f"Received 503 for {request.url}. Server overloaded, retrying with delay.")
            request.dont_filter = True
            return request
        
        # On successful response, reset 407 counter
        if 200 <= response.status < 400:
            if self.consecutive_407_count:
                self.consecutive_407_count = 0
        return response

    def _apply_proxy(self, request, spider, force_rotate: bool = False):
        # Allow a full proxy URL override: e.g. http://user:pass@host:port
        proxy_url_override = os.getenv("PROXY_URL", "").strip()
        proxy_user = os.getenv("PROXY_USER")
        proxy_pass = os.getenv("PROXY_PASS")
        proxy_auth_header: Optional[str] = None

        # Debug proxy configuration
        if not proxy_url_override and (not proxy_user or not proxy_pass):
            spider.logger.warning("Proxy credentials/URL not found - running without proxy")
            return

        # Prefer explicit proxy pool if provided
        if self.proxy_pool:
            proxy = random.choice(self.proxy_pool)
            spider.logger.debug(f"Using proxy from pool: {proxy}")
        else:
            if proxy_url_override:
                proxy = proxy_url_override
            else:
                # Webshare rotating gateway
                proxy_host = os.getenv("PROXY_HOST", "p.webshare.io")
                proxy_port = os.getenv("PROXY_PORT", "80")
                proxy = f"http://{proxy_host}:{proxy_port}"

        if not proxy_url_override and proxy_user and proxy_pass:
            # Add credentials to proxy URL
            try:
                parsed_no_auth = urlparse(proxy)
                host_port = f"{parsed_no_auth.hostname}:{parsed_no_auth.port or 80}"
                scheme = parsed_no_auth.scheme or "http"
                proxy = f"{scheme}://{proxy_user}:{proxy_pass}@{host_port}"
            except Exception:
                proxy = f"http://{proxy_user}:{proxy_pass}@{os.getenv('PROXY_HOST','p.webshare.io')}:{os.getenv('PROXY_PORT','80')}"

        prior_proxy = request.meta.get('proxy')
        if force_rotate or prior_proxy != proxy:
            request.meta['proxy'] = proxy
            try:
                # Avoid leaking credentials in logs
                parsed = urlparse(proxy)
                host_port = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
                spider.logger.info(f"Using proxy {host_port}")
            except Exception:
                spider.logger.info("Using proxy (masked)")
        
        # Also attach Proxy-Authorization header when credentials are available
        if not proxy_url_override and proxy_user and proxy_pass:
            token = base64.b64encode(f"{proxy_user}:{proxy_pass}".encode()).decode()
            request.headers['Proxy-Authorization'] = f"Basic {token}"
