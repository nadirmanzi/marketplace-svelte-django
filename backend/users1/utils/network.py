"""
Network utilities for the users app.

This module provides helper functions for handling network-related tasks,
such as extracting client IP addresses from requests while handling
proxy headers securely.
"""


def get_client_ip(request):
    """
    Get client IP address, handling proxy headers.

    Checks HTTP_X_FORWARDED_FOR header first to handle requests behind
    proxies or load balancers. If not present, falls back to REMOTE_ADDR.

    Args:
        request: Django request object

    Returns:
        str: IP address string (e.g. '127.0.0.1')
    """
    # Check X-Forwarded-For header (set by proxies/load balancers)
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        return x_forwarded_for.split(",")[0].strip()

    # Fall back to REMOTE_ADDR
    return request.META.get("REMOTE_ADDR", "")
