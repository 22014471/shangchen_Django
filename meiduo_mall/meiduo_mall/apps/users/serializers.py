import re
from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings
from celery_tasks.email.tasks import send_email_active
from goods.models import SKU
from . import constants

from .models import User, Address


class UserCreateCheckSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    sms_code = serializers.CharField(write_only=True)
    allow = serializers.CharField(write_only=True)
    token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2', 'sms_code', 'mobile', 'allow', "token")
        extra_kwargs = {
            "username": {
                "min_length": 5,
                "max_length": 20,
                "error_messages": {
                    "min_length": "用户名5-30个字符",
                    "max_length": "用户名5-30个字符"
                    }
            },
            "password": {
                "min_length": 8,
                "max_length": 20,
                "error_messages": {
                    "min_length": "密码8-30个字符",
                    "max_length": "密码8-30个字符"
                }
            }
        }

    def validate_mobile(self, value):
        if not re.match(r'1[3-9]\d{9}', value):
            raise serializers.ValidationError("手机号格式不正确")
        return value

    def validate_allow(self, value):
        if value != "true":
            raise serializers.ValidationError("请同意用户协议")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError("两次密码不一致")
        sms_code = attrs["sms_code"]
        mobile = attrs["mobile"]
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get("sms_%s" % mobile).decode()
        if not real_sms_code:
            raise serializers.ValidationError("无效的验证码")
        if sms_code != real_sms_code:
            raise serializers.ValidationError("短信验证码不正确")
        return attrs

    def create(self, validated_data):
        del validated_data["password2"]
        del validated_data["sms_code"]
        del validated_data["allow"]
        user = User.objects.create(**validated_data)
        user.save()
        user.set_password(validated_data["password"])
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token

        self.context['request'].user = user
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "mobile", "email", "username", "email_active")


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email")

    def update(self, instance, validated_data):
        instance = super().update(instance,validated_data)
        verify_url = instance.generate_verify_email_url()
        send_email_active.delay(instance.email, verify_url)
        return instance


class AddressSerializer(serializers.ModelSerializer):
    mobile = serializers.RegexField(regex=r"^1[3-9]\d{9}$")
    province = serializers.PrimaryKeyRelatedField(read_only=True)
    city = serializers.PrimaryKeyRelatedField(read_only=True)
    district = serializers.PrimaryKeyRelatedField(read_only=True)
    province_id = serializers.IntegerField(required=True)
    district_id = serializers.IntegerField(required=True)
    city_id = serializers.IntegerField(required=True)

    class Meta:
        model = Address
        fields = ("id", "receiver", "province", "province_id", "city", "city_id", "district", "district_id", "place", "mobile", "tel", "email", "title")

    def create(self, validated_data):
        print(validated_data)
        validated_data["user"] = self.context["request"].user
        print(validated_data)
        return super().create(validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("id", "title")


class AddUserBrowsingHistorySerializer(serializers.Serializer):
    """
    添加用户浏览历史序列化器
    """
    sku_id = serializers.IntegerField(label="商品SKU编号", min_value=1)

    def validate_sku_id(self, value):
        """
        检验sku_id是否存在
        """
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('该商品不存在')
        return value

    def create(self, validated_data):
        # sku_id
        sku_id = validated_data['sku_id']
        # user_id
        user = self.context['request'].user
        # redis  [6, 1,2,3,4,5]
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        redis_key = 'history_%s' % user.id
        # 去重
        pl.lrem(redis_key, 0, sku_id)
        # 保存 增加
        pl.lpush(redis_key, sku_id)
        # 截断
        pl.ltrim(redis_key, 0, constants.USER_BROWSING_HISTORY_COUNTS_LIMIT - 1)
        pl.execute()
        return validated_data

class SKUSerializer(serializers.ModelSerializer):
    """
    SKU序列化器
    """
    class Meta:
        model = SKU
        fields = ('id', 'name', 'price', 'default_image_url', 'comments')


