from django_redis import get_redis_connection
from rest_framework import serializers


class ImageCodeCheckSerializer(serializers.Serializer):
    image_code_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4,min_length=4)

    def validate(self, attrs):
        redis_conn = get_redis_connection('verify_codes')
        image_code_id = attrs["image_code_id"]
        text = attrs["text"]
        real_text = redis_conn.get('img_%s' % image_code_id)
        if not real_text:
            raise serializers.ValidationError("图片验证码已失效")
        real_text = real_text.decode()
        redis_conn.delete("img_%s" % image_code_id)
        if not real_text:
            raise serializers.ValidationError("图片验证码不存在")
        if real_text.lower() != text.lower():
            raise serializers.ValidationError("图片验证码不正确")
        mobile = self.context["view"].kwargs["mobile"]
        if redis_conn.get("send_sms_%s" % mobile):
            raise serializers.ValidationError("不能频繁访问")
        return attrs