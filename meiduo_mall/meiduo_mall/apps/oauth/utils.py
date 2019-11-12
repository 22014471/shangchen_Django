import json
from django.conf import settings
import urllib.parse
import urllib.request
import logging
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSerializer

from .exceptions import QQAPIError
from . import constants

logger = logging.getLogger("django")


def check_att_setting(obj, attr_name, error_msg):
    attr = getattr(obj, attr_name)
    if not attr:
        raise Exception("需要再设置中设置%s,内容为%s" % (attr_name, error_msg))
    return attr


class OAuthQQ:
    def __init__(self, client_id=None, redirect_uri=None, client_secret=None):
        self.client_id = client_id or check_att_setting(settings, "QQ_CLIENT_ID", "appid")
        self.redirect_uri = redirect_uri or check_att_setting(settings, "QQ_REDIRECT_URI", "回调网址")
        self.client_secret = client_secret or check_att_setting(settings, "QQ_CLIENT_SECRET", "网站的appkey")

    def get_login_qq_url(self, next):
        url = "https://graph.qq.com/oauth2.0/authorize?"
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": next
        }
        url += urllib.parse.urlencode(params)
        return url

    def get_access_token(self, code):
        url = "https://graph.qq.com/oauth2.0/token?"
        params = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        url += urllib.parse.urlencode(params)
        resp = urllib.request.urlopen(url)
        resp_str = resp.read().decode()

        # access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE14
        resp_dict = urllib.parse.parse_qs(resp_str)
        access_token = resp_dict.get("access_token")
        if not access_token:
            raise QQAPIError
        return access_token[0]

    def get_open_id(self, access_token):
        url = "https://graph.qq.com/oauth2.0/me?access_token=" + access_token
        resp = urllib.request.urlopen(url)
        # callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} );
        resp_str = resp.read().decode()
        try:
            resp_dict = json.loads(resp_str[10:-4])
        except Exception:
            logger.error("获取openid失败")
            raise QQAPIError
        openid = resp_dict.get("openid")
        return openid

    def get_return_token(self, openid):
        serializer = TJWSerializer(settings.SECRET_KEY, constants.LOGIN_QQ_EXPIRY_TIME)
        token = serializer.dumps({"openid": openid})
        token = token.decode()
        return token

    def check_user_token(self, token):
        serializer = TJWSerializer(settings.SECRET_KEY, constants.LOGIN_QQ_EXPIRY_TIME)
        try:
            data = serializer.loads(token)
        except Exception:
            return None
        else:
            openid = data.get("openid")
            return openid

