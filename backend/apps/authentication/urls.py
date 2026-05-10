from django.urls import path, include
from apps.authentication.views import RegisterView, LoginView, LogoutView, MeView


urlpatterns = [
    path('login/', LoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('register/', RegisterView.as_view(), name="register"),
    path('me/', MeView.as_view(), name="me"),
]