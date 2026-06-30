import logging
import uuid

logger = logging.getLogger('apps.common')


class RequestIDMiddleware:
    """
    Attaches a unique request ID to every incoming request and response
    header (X-Request-ID), so a single request can be traced across logs,
    error responses, and (if forwarded) downstream services.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID', uuid.uuid4().hex)
        request.request_id = request_id

        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response
