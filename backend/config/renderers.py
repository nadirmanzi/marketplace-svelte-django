from rest_framework.renderers import JSONRenderer


class StandardizedJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that wraps all successful responses in a consistent
    envelope structure: {"status": "success", "data": ...}.

    Error responses are already handled by the custom exception handler and
    will not be re-wrapped if they don't have a 2xx status code.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        # Only wrap successful 2xx responses
        if response and 200 <= response.status_code < 300:
            # Avoid double wrapping if already wrapped or if data is None
            if isinstance(data, dict) and "status" in data and "data" in data:
                formatted_data = data
            else:
                formatted_data = {"data": data}
            return super().render(formatted_data, accepted_media_type, renderer_context)

        # Error responses (4xx, 5xx) are returned as-is
        # (they are already standardized by custom_exception_handler)
        return super().render(data, accepted_media_type, renderer_context)
