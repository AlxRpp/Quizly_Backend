from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Normal JWTAuthentication from simplejwt reads the token from the
    Authorization header, but our frontend only has it in a httponly cookie.
    This class overwrites authenticate() to look in request.COOKIES instead,
    everything else (checking the token is valid etc) stays exactly like the
    parent class."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
