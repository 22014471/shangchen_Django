from django.shortcuts import render
from django.utils.decorators import method_decorator
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from cart.utils import after_login
from goods.models import SKU
from .serializers import UserCreateCheckSerializer, UserDetailSerializer, EmailSerializer, AddressSerializer, AddressTitleSerializer, \
    AddUserBrowsingHistorySerializer, SKUSerializer
from .models import User, Address
from . import constants
# Create your views here.


class UsernameView(APIView):
    """校验用户名"""
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        data = {
            "username": username,
            "count": count
        }
        return Response(data)


class MobileView(APIView):
    """校验手机号"""
    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        data = {
            "mobile": mobile,
            "count": count
        }
        return Response(data)

@method_decorator(after_login,name='post')
class UserCreateView(CreateAPIView):
    """用户注册"""
    serializer_class = UserCreateCheckSerializer


class UserDetailView(RetrieveAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class EmailView(UpdateAPIView):
    serializer_class = EmailSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    # 获取token值
    def get(self, request):
        token = request.query_params.get("token")
        if not token:
            return Response({"message": "缺少token"}, status=status.HTTP_400_BAD_REQUEST)
        # 根据token获取user
        user = User.verify_email_user(token)
        if not user:
            return Response({"message": "token不正确"}, status=status.HTTP_400_BAD_REQUEST)
        user.email_active = True
        user.save()
        return Response({"message": "ok"})


class AddressUserView(ModelViewSet):
    """用户地址"""
    serializer_class = AddressSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.addresses.filter(is_delete=False)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().all()
        serializer = AddressSerializer(queryset, many=True)
        user = self.request.user
        return Response({
            "addresses": serializer.data,
            "limit": constants.ADDRESS_PAGE_NUM,
            "default_address_id": user.default_address_id
        })

    def create(self, request, *args, **kwargs):
        count_num = self.get_queryset().count()
        if count_num >= constants.ADDRESS_MAX_ADD:
            return Response({"message":"添加地址达到上限"}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_delete = True
        instance.save()
        return Response({"message": "ok"}, status=status.HTTP_204_NO_CONTENT)

    @action(methods=["put"], detail=True)
    def title(self, request, *args, **kwargs):
        instance = self.get_object()
        self.serializer_class = AddressTitleSerializer
        serializer = self.get_serializer(instance, request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(methods=["put"], detail=True)
    def status(self, request, *args, **kwargs):
        instance = self.get_object()
        user = self.request.user
        user.default_address_id = instance.id
        user.save()
        return Response({"default_address_id":user.default_address_id})


class UserBrowsingHistoryView(CreateAPIView):
    """
    用户浏览历史记录
    """
    serializer_class = AddUserBrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取
        """
        user_id = request.user.id

        redis_conn = get_redis_connection("history")
        history = redis_conn.lrange("history_%s" % user_id, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        skus = []
        # 为了保持查询出的顺序与用户的浏览历史保存顺序一致
        for sku_id in history:
            sku = SKU.objects.get(id=sku_id)
            skus.append(sku)

        s = SKUSerializer(skus, many=True)
        return Response(s.data)