from django.utils.http import urlencode
from abc import ABC, abstractmethod
from django.core.cache import cache as default_cache
from django.conf import settings

class CacheKeyService:
    LIST_PREFIX = "document_list"

    @staticmethod
    def generate_detail_cache_key(pk):
        return f"document_detail_{pk}"
    
    @staticmethod
    def generate_list_cache_key(request=None):
        if request:
            params = request.query_params.dict()
            if params:
                query_string = urlencode(sorted(params.items()))
                return f"{CacheKeyService.LIST_PREFIX}?{query_string}"
            return f"{CacheKeyService.LIST_PREFIX}"
        return f"{CacheKeyService.LIST_PREFIX}*"
    

class AbstractDocumentCacheService(ABC):
    @abstractmethod
    def get_detail(self, pk: int):
        """Return cached detail data for a document PK, or None."""

    @abstractmethod
    def set_detail(self, pk: int, data: dict, timeout: int | None = None):
        """Cache detail data for a document PK."""

    @abstractmethod
    def get_list(self, request) -> dict | None:
        """Return cached list data for a given request, or None."""

    @abstractmethod
    def set_list(self, request, data: dict, timeout: int | None = None) -> None:
        """Cache list data keyed by the request's query params."""

    @abstractmethod
    def invalidate(self, pk: int | None = None) -> None:
        """
        Bust the detail cache for `pk` (if given) and sweep all list caches.
        Passing pk=None only busts list caches (e.g. after a bulk action).
        """



class DocumentCacheService(AbstractDocumentCacheService):

    def __init__(self, cache_backend=None, ttl: int | None = None):
        self._cache = cache_backend or default_cache
        self._ttl   = ttl or getattr(settings, 'DOCUMENT_CACHE_TTL', 2700)

    # ── reads ─────────────────────────────────────────────────────────────────

    def get_detail(self, pk: int):
        return self._cache.get(CacheKeyService.generate_detail_cache_key(pk))

    def get_list(self, request):
        return self._cache.get(CacheKeyService.generate_list_cache_key(request))

    # ── writes ────────────────────────────────────────────────────────────────

    def set_detail(self, pk: int, data: dict, timeout: int | None = None) -> None:
        self._cache.set(
            CacheKeyService.generate_detail_cache_key(pk),
            data,
            timeout=timeout or self._ttl,
        )

    def set_list(self, request, data: dict, timeout: int | None = None) -> None:
        self._cache.set(
            CacheKeyService.generate_list_cache_key(request),
            data,
            timeout=timeout or self._ttl,
        )

    # ── invalidation ─────────────────────────────────────────────────────────

    def invalidate(self, pk: int | None = None) -> None:
        keys = []
        if pk is not None:
            keys.append(CacheKeyService.generate_detail_cache_key(pk))
        list_keys = self._cache.keys(CacheKeyService.generate_list_cache_key())
        if list_keys:
            keys.extend(list_keys)
        if keys:
            self._cache.delete_many(keys)
