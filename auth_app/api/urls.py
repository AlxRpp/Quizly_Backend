from rest_framework_simplejwt.views import TokenObtainPairView
from django.urls import path
from .views import RegisterUserView, LoginAndSetCookiesView, LogoutAndDeleteCookiesView, CookieTokenRefreshView

urlpatterns = [

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginAndSetCookiesView.as_view(), name='login'),
    path('logout/', LogoutAndDeleteCookiesView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token-refresh')
]
