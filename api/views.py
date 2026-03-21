from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import logging
from api import settings

logger = logging.getLogger(settings.LOGGER)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.info("Health check requested.")
        return Response({"status": "healthy"}, status=status.HTTP_200_OK)


class homeview(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.info("Home view requested.")
        return Response({"message": "Welcome to the API"}, status=status.HTTP_200_OK)
