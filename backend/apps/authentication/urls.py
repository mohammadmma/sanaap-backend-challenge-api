from django.urls import path, include
from apps.authentication.views import ViewerRegisterView, LoginView, LogoutView, MeView, AdminDemadView


urlpatterns = [
    path('login/', LoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('register/', ViewerRegisterView.as_view(), name="register"),
    path('admin-demand/', AdminDemadView.as_view(), name="admin-demand"),
    path('me/', MeView.as_view(), name="me"),
]