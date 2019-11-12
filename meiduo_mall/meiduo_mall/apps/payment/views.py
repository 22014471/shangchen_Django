import os

from alipay import AliPay
from django.conf import settings
from django.shortcuts import render
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import OrderInfo
from payment.models import Payment


class PaymentView(APIView):
    """
    支付
    """
    permission_classes = (IsAuthenticated,)

    # GET /orders/(?P<order_id>\d+)/payment/
    def get(self,request, order_id):
        # 判断订单是否正确
        user = request.user
        try:
            order = OrderInfo.objects.get(
                order_id=order_id,
                user=user,
                pay_method=OrderInfo.PAY_METHODS_ENUM['ALIPAY'],
                status = OrderInfo.ORDER_STATUS_ENUM['UNPAID']
            )
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)
        # 向支付宝获取给用户支付页面的链接请求
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                     "keys/alipay_public_key.pem"),             # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug = settings.ALIPAY_DEBUG,  # 默认False
        )
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id, # 订单编号
            total_amount=str(order.total_amount + order.freight),
            subject="测试订单,美多商城%s" % order_id,
            return_url="http://www.meiduo.site:8080/pay_success.html",
            # notify_url="https://example.com/notify",  # 可选, 不填则使用默认notify url
        )
        # 返回alipay_url
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        return Response({'alipay_url': alipay_url})

# PUT /payment/status/?<支付宝参数>
class PaymentStatusView(APIView):
    def put(self, request):
        # 接受参数
        ali_data = request.query_params.dict()
        signature = ali_data.pop("sign")
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                "keys/alipay_public_key.pem"),
            sign_type="RSA2",
            debug=settings.ALIPAY_DEBUG,
        )
        # verification 校验参数
        success = alipay.verify(ali_data, signature)
        if success:
            order_id = ali_data['out_trade_no']
            trade_id = ali_data['trade_no'] # 支付宝交易号
            print("trade succeed")
            # 保存数据
            #   保存支付结果数据Payment
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id
            )
            #  修改订单状态
            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])
            return Response({'trade_id': trade_id})
        else:
            return Response({'message': '参数有误'}, status=status.HTTP_400_BAD_REQUEST)
