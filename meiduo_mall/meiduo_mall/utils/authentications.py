from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class NoExceptionJSONWebTokenAuthentication(JSONWebTokenAuthentication):
    """自定义认证类"""
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except Exception:
            return None

