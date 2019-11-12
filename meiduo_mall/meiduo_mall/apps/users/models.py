from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import BadData
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSerializer

from . import constants
from oauth.models import BasicModel
# Create your models here.


class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    email_active = models.BooleanField(default=False, verbose_name="邮箱验证状态")
    default_address = models.ForeignKey('Address', null=True, blank=True, related_name="users", on_delete=models.SET_NULL, verbose_name="默认地址")

    class Meta:
        db_table = "tb_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def generate_verify_email_url(self):
        serializer = TJWSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_ACTIVE_TIME)
        data = {
            "id": self.id,
            "email": self.email
        }
        token = serializer.dumps(data).decode()
        verify_url = "http://www.meiduo.site:8080/success_verify_email.html?token=" + token
        return verify_url

    @staticmethod
    def verify_email_user(token):
        serializer = TJWSerializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_ACTIVE_TIME)
        try:
            user_data = serializer.loads(token)
        except BadData:
            return None
        user_email = user_data.get("email")
        user_id = user_data.get("id")
        try:
            user = User.objects.get(id=user_id, email=user_email)
        except User.DoesNotExist:
            return None
        return user

    def __str__(self):
        return self.username

class Address(BasicModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses",
                             verbose_name="用户")
    title = models.CharField(max_length=20, verbose_name="地址名称")
    receiver = models.CharField(max_length=20, verbose_name="收件人")
    province = models.ForeignKey('areas.Areas', on_delete=models.PROTECT, related_name="province_address", verbose_name="省")
    city = models.ForeignKey('areas.Areas', on_delete=models.PROTECT, related_name="city_address", verbose_name="市")
    district = models.ForeignKey('areas.Areas', on_delete=models.PROTECT, related_name="district_address", verbose_name="区")
    place = models.CharField(max_length=50, verbose_name="地址")
    mobile = models.CharField(max_length=11, verbose_name="手机")
    tel = models.CharField(max_length=20, null=True, blank=True, default="", verbose_name="固定电话")
    email = models.CharField(max_length=30, null=True, blank=True, default="", verbose_name="邮箱")
    is_delete = models.BooleanField(default=False, verbose_name="是否删除")

    class Meta:
        db_table = "tb_address"
        verbose_name = "地址"
        verbose_name_plural = verbose_name
        ordering = ["-update_time"]

    def __str__(self):
        return self.name


