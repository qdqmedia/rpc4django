import base64
from functools import wraps
from django.contrib.auth import authenticate, login
from .exceptions import ProcessingException


class AuthException(ProcessingException):
    code = 403


def basic_http_auth(request):
    # Already authenticated user
    user = getattr(request, 'user', None)
    if user and user.is_authenticated():
        return request
    # HTTP auth
    if 'HTTP_AUTHORIZATION' not in request.META:
        raise AuthException('Authentication required')
    auth = request.META['HTTP_AUTHORIZATION'].split()
    if len(auth) != 2:
        raise AuthException('Wrong HTTP_AUTHORIZATION header')
        # NOTE: We are only support basic authentication for now.
    if auth[0].lower() != "basic":
        raise AuthException('We support only basic http auth')
    username, password = base64.b64decode(auth[1]).split(':')
    user = authenticate(username=username, password=password)
    if user is None:
        raise AuthException('Wrong user.')
    if not user.is_active:
        raise AuthException('Wrong user.')
    login(request, user)
    request.user = user
    return request


def staff_required(request):
    user = getattr(request, 'user', None)
    if not user:
        raise AuthException('User not authenticated')
    if not (user.is_staff or user.is_superuser):
        raise AuthException('User does not have permissions')


def permissions_required(permissions):
    @wraps
    def foo(request):
        user = getattr(request, 'user', None)
        if not user:
            raise AuthException('User not authenticated')
        if not user.has_perm(permissions):
            raise AuthException('User does not have permissions')
    return foo
