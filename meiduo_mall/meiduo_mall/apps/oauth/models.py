from django.db import models


# Create your models here.

class BasicModel(models.Model):
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuthQQUser(BasicModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    openid = models.CharField(db_index=True, max_length=64)

    class Meta:
        db_table = "auth_qq_user"
        verbose_name = "QQ登陆用户数据"
        verbose_name_plural = verbose_name




