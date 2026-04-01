from rest_framework import generics

from api.permissions import IsAuthenticatedWithRole
from .serializers import UserProfileSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get and update the currently authenticated user's profile.
    """

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedWithRole]

    def get_object(self):
        return self.request.user
