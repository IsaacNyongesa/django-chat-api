"""
Centralized exception handling so every error response from the API has the
same shape, regardless of where it was raised:

    {
        "error": {
            "code": "validation_error",
            "message": "Human readable summary.",
            "details": {...}   # optional, field-level errors etc.
        }
    }

This is what a frontend team will thank you for — they can write one error
parser instead of branching on a dozen ad-hoc shapes.
"""
import logging
import uuid

from django.db import DatabaseError
from django.http import Http404
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('apps.common')


def _error_code_for(exc) -> str:
    mapping = {
        'ValidationError': 'validation_error',
        'AuthenticationFailed': 'authentication_failed',
        'NotAuthenticated': 'not_authenticated',
        'PermissionDenied': 'permission_denied',
        'NotFound': 'not_found',
        'MethodNotAllowed': 'method_not_allowed',
        'Throttled': 'rate_limited',
        'ParseError': 'parse_error',
    }
    return mapping.get(exc.__class__.__name__, 'error')


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    request = context.get('request')
    error_id = uuid.uuid4().hex[:12]

    if response is not None:
        # Normalize DRF's default {field: [...]} / {detail: ...} shapes
        if isinstance(response.data, dict) and 'detail' in response.data:
            details = None
            message = str(response.data['detail'])
        else:
            details = response.data
            message = 'One or more fields failed validation.'

        response.data = {
            'error': {
                'code': _error_code_for(exc),
                'message': message,
                'details': details,
                'error_id': error_id,
            }
        }
        if response.status_code >= 500:
            logger.error('API 5xx [%s]: %s', error_id, exc, exc_info=True)
        else:
            logger.info('API %s [%s]: %s', response.status_code, error_id, exc)
        return response

    # Unhandled exceptions (DRF returned None) — never leak a stack trace to the client.
    if isinstance(exc, Http404):
        return Response(
            {'error': {'code': 'not_found', 'message': 'Resource not found.', 'error_id': error_id}},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, DatabaseError):
        logger.error('Unhandled DB error [%s]: %s', error_id, exc, exc_info=True)
        return Response(
            {'error': {'code': 'database_error', 'message': 'A database error occurred.', 'error_id': error_id}},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    logger.error('Unhandled exception [%s]: %s', error_id, exc, exc_info=True)
    return Response(
        {'error': {
            'code': 'internal_error',
            'message': 'An unexpected error occurred. Please try again or contact support.',
            'error_id': error_id,
        }},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
