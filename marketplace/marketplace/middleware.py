import time

from django.conf import settings
from django.http import HttpResponse
from django.urls import resolve


class RateLimitMiddleware:
    """Per-IP rate limiting for sensitive endpoints (login, signup, password reset).

    Uses an in-memory cache. In production with multiple workers, replace
    with a shared store (Redis / Memcached) for accurate cross-process limiting.
    """

    # Class-level store shared across requests within the same process.
    _request_log = {}

    def __init__(self, get_response):
        self.get_response = get_response
        self.rules = getattr(settings, 'RATE_LIMIT_RULES', {})

    def __call__(self, request):
        if request.method == 'POST':
            try:
                match = resolve(request.path)
                url_name = match.url_name
            except Exception:
                url_name = None

            if url_name and url_name in self.rules:
                max_requests, window = self.rules[url_name]
                client_ip = self._get_client_ip(request)
                cache_key = f'rl:{url_name}:{client_ip}'

                if self._is_rate_limited(cache_key, max_requests, window):
                    return HttpResponse(
                        'Too many requests. Please try again later.',
                        status=429,
                        content_type='text/plain',
                    )

                self._record_request(cache_key)

        return self.get_response(request)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP, respecting X-Forwarded-For behind a proxy."""
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

    @classmethod
    def _is_rate_limited(cls, key, max_requests, window):
        now = time.time()
        entries = cls._request_log.get(key, [])
        # Keep only entries within the current window.
        entries = [t for t in entries if t > now - window]
        cls._request_log[key] = entries
        return len(entries) >= max_requests

    @classmethod
    def _record_request(cls, key):
        cls._request_log.setdefault(key, []).append(time.time())

    @classmethod
    def reset(cls):
        """Clear the in-memory request log (useful in tests)."""
        cls._request_log.clear()
