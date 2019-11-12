from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as rsf_exception_handler
from django.db import DatabaseError
from redis.exceptions import RedisError
import logging

logger = logging.getLogger("django")


def exception_handler(exc, context):
    response = rsf_exception_handler(exc, context)
    if response is None:
        view = context["view"]
        if isinstance(exc, DatabaseError) or isinstance(exc, RedisError):
            logger.error("[%s]:%s" % (view, exc))
            response = Response({"message":"服务器内部错误"}, status=status.HTTP_507_INSUFFICIENT_STORAGE)
    return response