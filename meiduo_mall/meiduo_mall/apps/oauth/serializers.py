from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from .utils import OAuthQQ
from users.models import User
from .models import AuthQQUser


class AuthQQUserSerializer(serializers.ModelSerializer):
    sms_code = serializers.CharField(write_only=True)
    access_token = serializers.CharField(write_only=True)
    mobile = serializers.RegexField(regex=r"1[3-9]\d{9}")
    token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "mobile", "sms_code", "password", "access_token", "username", "token")
        extra_kwargs = {
            "username": {"read_only": True},
            "password": {
                "max_length": 20,
                "min_length": 8,
                "write_only": True
            }
        }

    def validate(self, attrs):
        mobile = attrs["mobile"]
        sms_code = attrs["sms_code"]
        redis_coon = get_redis_connection("verify_codes")
        real_sms_code = redis_coon.get("sms_%s" % mobile)
        if not real_sms_code:
            raise serializers.ValidationError("短信验证码已失效")
        real_sms_code = real_sms_code.decode()
        if sms_code != real_sms_code:
            raise serializers.ValidationError("短信验证码不正确")
        access_token = attrs["access_token"]
        oauth = OAuthQQ()
        openid = oauth.check_user_token(access_token)
        if not openid:
            raise serializers.ValidationError("access_token已失效")
        attrs["openid"] = openid
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoseNotExist:
            raise serializers.ValidationError("密码错误")
        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        user = validated_data.get("user")
        openid = validated_data.get("openid")
        mobile = validated_data.get("mobile")
        password = validated_data.get("password")
        if not user:
            user = User.objects.create_user(mobile=mobile, password=password, username=mobile)
        AuthQQUser.objects.create(user=user, openid=openid)
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        self.context['request'].user = user
        return user


