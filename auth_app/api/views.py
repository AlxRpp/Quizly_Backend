from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import RegisterUserSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
User = get_user_model()


class RegisterUserView(APIView):
    """Create a new user account."""
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Returns:
            201 with {"detail": ...} on success.
            400 with the serializer's validation errors otherwise.
        """
        serializer = RegisterUserSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User created successfully!"}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAndSetCookiesView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Log in and set the tokens as httponly cookies instead of
        returning them in the response body.

        Returns:
            200 with {"detail": ..., "user": {id, username, email}} on success.
            401 with an error message if the credentials are invalid.
        """
        self.response = super().post(request, *args, **kwargs)
        try:
            refresh = self.response.data.get('refresh')
            access = self.response.data.get('access')

            self.response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                secure=True,
                samesite="Lax"
            )

            self.response.set_cookie(
                key="access_token",
                value=str(access),
                httponly=True,
                secure=True,
                samesite="Lax"
            )
            user = User.objects.get(username=request.data.get('username'))
            self.response.data = {
                "detail": "Login successfully!",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }

            return self.response

        except User.DoesNotExist:
            return Response({"error": "Unvalid Credentials!"},
                            status=status.HTTP_401_UNAUTHORIZED)


class LogoutAndDeleteCookiesView(APIView):
    """Blacklist the refresh_token and delete both auth cookies."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Returns:
            200 with a confirmation detail message.
        """
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass
        response = Response({
            "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
        }, status=status.HTTP_200_OK)
        response.delete_cookie(key="refresh_token")
        response.delete_cookie(key="access_token")

        return response


class CookieTokenRefreshView(TokenRefreshView):

    def post(self, request, *args, **kwargs):
        """Refresh the access token using the refresh_token httponly cookie
        (instead of the request body, unlike the default TokenRefreshView).

        Returns:
            401 if the cookie is missing, or the refresh token is invalid/blacklisted.
            200 with a new access_token cookie set, otherwise.
        """
        refresh = request.COOKIES.get("refresh_token")

        if refresh is None:
            return Response({"detail": "Cookie not found"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data={"refresh": refresh})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:
            return Response({"message": "Token is unvalid"}, status=status.HTTP_401_UNAUTHORIZED)

        accessToken = serializer.validated_data.get("access")

        response = Response({"detail": "Token refreshed"})

        response.set_cookie(
            key="access_token",
            value=accessToken,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        return response
