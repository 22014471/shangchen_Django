import base64
import pickle

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer, CartSelectAllSerializer
from cart.utils import CartMixin
from goods.models import SKU
from . import constants

class CartView(CartMixin, APIView):
    """购物车"""

    # 当点击加入购物车时触发 POST /cart/
    def post(self,request):
        """添加购物车"""
        # 接收参数(sku_id,count,selected)
        # 校验参数（序列化器）
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data['sku_id']
        count = serializer.validated_data['count']
        selected = serializer.validated_data['selected']
        # cookie  string  {cart : {sku_id1:[ count, seleted ],sku_id2:[ count, seleted ] } }
        #
        # redis   string  {cart_user_id : {sku_id1:[ count, seleted ],sku_id2:[ count, seleted ] } }
        sku_id = str(sku_id)
        # cart_dict = self.read_cart(request)
        cart_dict = request.cart
        cart_dict[sku_id] =cart_dict.get(sku_id,None)
        if cart_dict[sku_id]:
            cart_dict[sku_id][0] += count
        else:
            cart_dict[sku_id] = [0, ""]
            cart_dict[sku_id][0] = count
        cart_dict[sku_id][1] = selected

        # response = Response(serializer.data, status=status.HTTP_201_CREATED)
        # self.write_cart(request, cart_dict, response)
        # return response
        return Response(serializer.data, status=status.HTTP_201_CREATED)



    #  GET /cart/
    def get(self,request):
        """cart_data"""
        # cart_dict = self.read_cart(request)
        cart_dict = request.cart
        cart_sku_list = SKU.objects.filter(id__in=cart_dict.keys())
        for sku in cart_sku_list:
            sku.count = cart_dict[str(sku.id)][0]
            sku.selected = cart_dict[str(sku.id)][1]
        serializer = CartSKUSerializer(cart_sku_list, many=True)
        return Response(serializer.data)


    def put(self,request):
        """
        修改购物车数据
        """
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        sku_id = str(sku_id)
        # cart_dict = self.read_cart(request)
        cart_dict = request.cart
        cart_dict[sku_id] = [ count, selected ]
        # response = Response(serializer.data)
        # self.write_cart(request, cart_dict, response)
        # return response
        return Response(serializer.data)

    def delete(self, request):
        """
       删除购物车数据
       """
        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data['sku_id']

        cart_dict = request.cart
        sku_id = str(sku_id)
        cart_dict.pop(sku_id, None)

        # response = Response(status=status.HTTP_204_NO_CONTENT)
        # self.write_cart(request, cart_dict, response)
        # return response
        return Response(serializer.data)

# PUT /cart/selection/
class CartSelectAllView(CartMixin, APIView):
    """
    购物车全选
    """
    def put(self,request):
        serializer = CartSelectAllSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data['selected']

        cart_dict = request.cart
        if selected:
            for sku_id in cart_dict:
                cart_dict[sku_id][1] = selected
        return Response({"message": "OK"})


