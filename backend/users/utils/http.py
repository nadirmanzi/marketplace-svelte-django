"""
HTTP and network utilities for the users application.
"""

def get_client_ip(request):
    """
    Extract client IP address from a Django request object.
    
    Handles proxy headers (HTTP_X_FORWARDED_FOR) and direct connections.
    
    Args:
        request: Django HttpRequest object.
    
    Returns:
        str: Client IP address or None if not found.
    """
    if not request:
        return None
        
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take first IP in chain (client IP)
        return x_forwarded_for.split(',')[0].strip()
    
    return request.META.get('REMOTE_ADDR')
