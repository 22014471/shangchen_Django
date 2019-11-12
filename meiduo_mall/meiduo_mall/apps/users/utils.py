import re

from django.contrib.auth.backends import ModelBackend

from .models import User


def jwt_response_payload_handler(token, user=None, request=None):
    request.user = user
    return {
        "token": token,
        "user_id": user.id,
        "username": user.username
    }


def get_user_by_account(account):
    if re.match(r'1[3-9]\d{9}', account):
        user_query = User.objects.filter(mobile=account)
        return user_query


class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user_query = User.objects.filter(username=username)
        if user_query and user_query.get().check_password(password):
            return user_query.get()
        user_query = get_user_by_account(username)
        if user_query and user_query.get().check_password(password):
            return user_query.get()
