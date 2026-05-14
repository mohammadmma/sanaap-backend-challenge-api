from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django.contrib.auth.models import Group
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.authentication.permissions import IsAdmin, IsEditor, IsViewer
from rest_framework import status, serializers
from django.contrib.auth import get_user_model
from apps.authentication.serializers import RegisterValidator, UserReadSerializer, UserWriteSerializer
from apps.authentication.models import AdminRequestModel
from django.db import transaction
from apps.authentication.services import UserService
from django_filters.rest_framework import  DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from apps.authentication.filters import UserFilter
from apps.authentication.pagination import StandardResultsSetPagination
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import OpenApiResponse, OpenApiExample, OpenApiParameter


User = get_user_model()



@extend_schema(
    tags=["Authentication"],
    summary="Register and request admin access",
    description="Registers user as viewer and creates a pending admin request.",
    request=RegisterValidator,
    responses={
        201: OpenApiResponse(
            description="Admin request created",
            response={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "user": {"type": "object"}
                }
            }
        ),
    }
)
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
            
class UserCRUDModelViewSet(ModelViewSet):
    permission_classes = [IsAdmin]
    def get_queryset(self):
        return (
            User.objects
            .prefetch_related('groups').all()
        )

    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """Read actions use ReadSerializer, write actions use WriteSerializer."""
        if self.action in ('list', 'retrieve'):
            return UserReadSerializer
        return UserWriteSerializer

    def perform_create(self, serializer):
        UserService.create_user(serializer.validated_data.copy())

    def perform_update(self, serializer):
        UserService.update_user(serializer.instance, serializer.validated_data.copy())


    @extend_schema(
    tags=["User Management"],
    summary="List users",
    description="Returns paginated list of users with filtering.",
    parameters=[
        OpenApiParameter(name="is_active", type=bool),
        OpenApiParameter(name="username", type=str),
        OpenApiParameter(name="joined_after", type=str),
        OpenApiParameter(name="joined_before", type=str),
        OpenApiParameter(name="role", type=str),
        OpenApiParameter(name="page", type=int),
        OpenApiParameter(name="page_size", type=int),
    ],
    responses={200: UserReadSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    

    @extend_schema(
    tags=["User Management"],
    summary="Retrieve user",
    responses={200: UserReadSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
    tags=["User Management"],
    summary="Create user",
    request=UserWriteSerializer,
    responses={201: UserReadSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
    tags=["User Management"],
    summary="Update user",
    request=UserWriteSerializer,
    responses={200: UserReadSerializer}
    )
    def update(self, request, *args, **kwargs):
        target_user = self.get_object()
        target_groups = target_user.groups.values_list('name', flat=True).first()
        if target_user.is_superuser or target_groups == 'admin':
            return Response("You can not manipulate this user", status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
    tags=["User Management"],
    summary="Update user",
    request=UserWriteSerializer,
    responses={200: UserReadSerializer}
    )
    def partial_update(self, request, *args, **kwargs):
        target_user = self.get_object()
        target_groups = target_user.groups.values_list('name', flat=True).first()
        if target_user.is_superuser or target_groups == 'admin':
            return Response("You can not manipulate this user", status=status.HTTP_400_BAD_REQUEST)
        return super().partial_update(request, *args, **kwargs)


    @extend_schema(
    tags=["User Management"],
    summary="Delete user",
    responses={
        204: OpenApiResponse(description="User deleted"),
        400: OpenApiResponse(description="Cannot delete yourself")
    }
    )
    def destroy(self, request, *args, **kwargs):
        target_user = self.get_object()
        target_groups = target_user.groups.values_list('name', flat=True).first()
        if target_user.is_superuser or target_groups == 'admin':
            return Response("You can not manipulate this user", status=status.HTTP_400_BAD_REQUEST)
        try:
            UserService.delete_user(request.user, target_user)
        except ValueError as e:
            raise serializers.ValidationError({'error': str(e)})
        return Response(
            {'message': f'User ({target_user.username}) deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


@extend_schema(
    tags=["Authentication"],
    summary="Register viewer",
    description="Registers a new user with 'viewer' role and logs them in.",
    request=RegisterValidator,
    responses={
        201: OpenApiResponse(
            description="User created",
            response={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "user": {"type": "object"}
                }
            }
        ),
    }
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


@extend_schema(
    tags=["Authentication"],
    summary="Login user",
    description="Authenticates user using username and password and starts a session.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string"}
            },
            "required": ["username", "password"]
        }
    },
    responses={
        200: OpenApiResponse(
            description="Login successful",
            response={
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "user": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "username": {"type": "string"},
                            "role": {"type": "string"}
                        }
                    }
                }
            }
        ),
    }
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
            'Invalid credentials',
            status=status.HTTP_401_UNAUTHORIZED
        )


@extend_schema(
    tags=["Authentication"],
    summary="Logout user",
    description="Logs out the currently authenticated user.",
    responses={
        200: OpenApiResponse(
            description="Logout successful",
            response={"type": "object", "properties": {"message": {"type": "string"}}}
        ),
    }
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out successfully'})



@extend_schema(
    tags=["Authentication"],
    summary="Get current user",
    description="Returns the currently authenticated user's basic info.",
    responses={
        200: OpenApiResponse(
            description="User info",
            response={
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "username": {"type": "string"},
                    "role": {"type": "string"}
                }
            }
        ),
    }
)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'role': user.groups.values_list('name', flat=True).first(),
        })