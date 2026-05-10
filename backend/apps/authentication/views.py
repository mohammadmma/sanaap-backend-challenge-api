from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from django.contrib.auth.models import Group
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.authentication.serializers import RegisterValidator
from apps.authentication.models import AdminRequestModel
from django.db import transaction


User = get_user_model()



class AdminDemadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterValidator(data=request.data)
        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                user = User.objects.create_user(**serializer.validated_data)

                viewer_group, _ = Group.objects.get_or_create(name='viewer')
                user.groups.add(viewer_group)

                login(request, user)

                AdminRequestModel.objects.create(user=user)
                return Response(
                    {
                        'message': 'Registered as viewer. Admin request is pending superuser approval.',
                        'user': {'id': user.id, 'username': user.username, 'role': user.groups.values_list('name', flat=True).first()},
                    },
                    status=status.HTTP_201_CREATED
                )

class ViewerRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterValidator(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = User.objects.create_user(**serializer.validated_data)

            viewer_group, _ = Group.objects.get_or_create(name='viewer')
            user.groups.add(viewer_group)

            login(request, user)

            return Response(
            {
                'message': 'User registered and logedin successfully.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.groups.values_list('name', flat=True).first(),
                }
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response({
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.groups.values_list('name', flat=True).first(),
                }
            })
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'role': user.groups.values_list('name', flat=True).first(),
        })