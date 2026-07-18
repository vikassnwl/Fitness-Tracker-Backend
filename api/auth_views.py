from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


def user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''
        email = (request.data.get('email') or '').strip()

        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(password) < 6:
            return Response(
                {'detail': 'Password must be at least 6 characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username__iexact=username).exists():
            return Response(
                {'detail': 'That username is already taken.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(username=username, password=password, email=email)
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {'token': token.key, 'user': user_payload(user)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''

        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': user_payload(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(user_payload(request.user))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({'detail': 'Logged out.'})
