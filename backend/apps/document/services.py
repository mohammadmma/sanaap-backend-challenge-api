from django.utils.http import urlencode

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
