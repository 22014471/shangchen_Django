import logging
import random

from django.http import HttpResponse
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from celery_tasks.sms.utils.yuntongxun.sms import CCP
from meiduo_mall.libs.captcha.captcha import captcha
from . import constants
from .serializers import ImageCodeCheckSerializer
from celery_tasks.sms.tasks import send_sms_code

logger = logging.getLogger('django')


class ImageCodeView(APIView):
    """图片验证码"""
    def get(self, request, image_code_id):
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_TIME, text)
        return HttpResponse(image, content_type="image/jpg")


class SMSCodeView(GenericAPIView):
    """短信验证码"""
    serializer_class = ImageCodeCheckSerializer

    def get(self, request, mobile):
        # 手机号、text、UUID
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        redis_conn = get_redis_connection('verify_codes')
        sms_code = "%06d" % random.randint(0, 999999)

        # 在发送短信验证码前保存数据，以免同一个图片验证码，多次访问
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_TIME, sms_code)
        pl.setex("send_sms_%s" % mobile, constants.SEND_SMS_CODE_TIME, 1)
        pl.execute()

        # try:
        #     ccp = CCP()
        #     result = ccp.send_template_sms(mobile, [sms_code, constants.IMAGE_CODE_TIME//60], constants.SMS_CODE_TEMP_ID)
        # except Exception as e:
        #     logger.error("短信验证码发送失败[%s]:%s" % (mobile, e))
        #     return Response({"message": "failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # if result != 0:
        #     logger.error("短信验证码发送失败[%s]" % mobile)
        #     return Response({"message": "failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # logger.error("短信验证码发送成功[%s]" % mobile)
        send_sms_code.delay(mobile, sms_code, constants.IMAGE_CODE_TIME//60, constants.SMS_CODE_TEMP_ID)
        return Response({"message": "ok"})