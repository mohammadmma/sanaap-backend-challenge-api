from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.authentication.views import (
    ViewerRegisterView,
    LoginView,
    LogoutView,
    MeView,
    AdminDemadView,
    UserCRUDModelViewSet,
    )

api_router = DefaultRouter()
api_router.register(r"user-crud", UserCRUDModelViewSet, basename="user_crud")


urlpatterns = [
    path('login/', LoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name="logout"),
    path('register/', ViewerRegisterView.as_view(), name="register"),
    path('admin-demand/', AdminDemadView.as_view(), name="admin_demand"),
    path('me/', MeView.as_view(), name="me"),

    path("", include(api_router.urls)),
]