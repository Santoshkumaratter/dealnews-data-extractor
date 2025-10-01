import sys

# ✅ MacOS reactor fix for Scrapy + Twisted
if sys.platform == "darwin":
    import twisted.internet.asyncioreactor
    try:
        twisted.internet.asyncioreactor.install()
    except Exception:
        pass
