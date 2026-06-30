import logging

from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.views import View
import redis
from django.conf import settings

logger = logging.getLogger('apps.common')


class HealthCheckView(View):
    """Liveness probe — process is up. Does not touch dependencies."""

    def get(self, request):
        return JsonResponse({'status': 'ok'})


class ReadinessCheckView(View):
    """
    Readiness probe — verifies the app can actually serve traffic by
    checking its hard dependencies (DB, Redis). Used by load balancers /
    k8s to decide whether to route traffic to this instance.
    """

    def get(self, request):
        checks = {'database': self._check_db(), 'redis': self._check_redis()}
        healthy = all(checks.values())
        return JsonResponse({'status': 'ok' if healthy else 'unavailable', 'checks': checks},
                             status=200 if healthy else 503)

    def _check_db(self):
        try:
            connections['default'].cursor()
            return True
        except OperationalError:
            logger.error('Readiness check: database unreachable', exc_info=True)
            return False

    def _check_redis(self):
        try:
            client = redis.from_url(settings.REDIS_URL)
            return client.ping()
        except Exception:
            logger.error('Readiness check: redis unreachable', exc_info=True)
            return False
