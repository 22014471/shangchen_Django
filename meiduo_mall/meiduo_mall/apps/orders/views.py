from decimal import Decimal
from django.shortcuts import render

# GET /orders/settlement/
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.utils import CartMixin
from goods.models import SKU
from orders.serializers import OrderSettlementSerializer, SaveOrderSerializer


class OrderSettlementView(CartMixin,APIView):
    """
    订单结算
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        获取
        """
        # 从购物车中获取用户勾选要结算的商品信息
        # redis   string  {cart_user_id : {sku_id1:[ count, seleted ],sku_id2:[ count, seleted ] } }
        cart = request.cart
        # 查询商品信息
        sku_id_list = []
        for sku_id in cart.keys():
            if cart[sku_id][1] == True:
                sku_id_list.append(int(sku_id))
        skus = SKU.objects.filter(id__in=sku_id_list)
        for sku in skus:
            sku.count = cart[str(sku.id)][0]

        # 运费
        freight = Decimal('10.00')

        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        return Response(serializer.data)

# POST /orders/
class SaveOrderView(CreateAPIView):
    """
    保存订单
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SaveOrderSerializer
