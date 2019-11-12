from django.shortcuts import render
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings

from cart.utils import after_login
from .utils import OAuthQQ
from .exceptions import QQAPIError
from .models import AuthQQUser
from .serializers import AuthQQUserSerializer
# Create your views here.

class OAuthQQView(APIView):
    """QQ第三方登陆ｕｒｌ"""
    def get(self, request):
        next = request.query_params.get("next")
        # 获取访问qq登陆的url
        oauth = OAuthQQ()
        url = oauth.get_login_qq_url(next)
        return Response({"login_url": url})

@method_decorator(after_login,name='post')
@method_decorator(after_login,name='get')
class AuthUserView(CreateAPIView):
    """"""
    serializer_class = AuthQQUserSerializer

    def get(self, request):
        code = request.query_params.get("code")
        oauth = OAuthQQ()
        try:
            access_token = oauth.get_access_token(code)
            openid = oauth.get_open_id(access_token)
        except QQAPIError:
            return Response({"message": "内部信息错误"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            query_user = AuthQQUser.objects.get(openid=openid)
        except AuthQQUser.DoesNotExist:
            # 用户不存在，之前没有登陆过，生成access_token返回
            token = oauth.get_return_token(openid)
            return Response({'access_token': token})
        else:
            user = query_user.user
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            data = {
                "user_id": user.id,
                "username": user.username,
                "token": token
            }
            return Response(data)
