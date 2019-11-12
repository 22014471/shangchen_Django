import base64
import pickle

from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework.views import APIView

from cart import constants


class CartMixin():
    """购物车扩展类"""
    decoder = (str.encode, base64.b64decode, pickle.loads)
    encoder = (pickle.dumps, base64.b64encode, bytes.decode)

    def read_cart(self,request):
        if request.user and request.user.is_authenticated:
            return self.read_cart_from_redis(request.user.id)
        else:
            return self.read_cart_from_cookie(request)


    def write_cart(self,request,cart_dict, response):
        if request.user and request.user.is_authenticated:
            return self.write_cart_to_redis(request.user.id, cart_dict)
        else:
            return self.write_cart_to_cookie(cart_dict, response)

    def read_cart_from_redis(self, user_id):
        redis_conn = get_redis_connection('cart')
        key = "cart_%s" % user_id
        cart_bytes = redis_conn.get(key)
        if not cart_bytes:
            return {}
        cart_dict = pickle.loads(cart_bytes)
        return cart_dict


    def read_cart_from_cookie(self,request):
        cart_dict = request.COOKIES.get('cart')
        print('cookie_cart-------------->',cart_dict)
        if not cart_dict:
            return {}
        for operate in self.decoder:
            cart_dict = operate(cart_dict)
        return cart_dict

    # cookie  string  {cart: {sku_id1:[ count, seleted ],sku_id2:[ count, seleted ] } }
    #
    # redis   string  {cart_user_id : {sku_id1:[ count, seleted ],sku_id2:[ count, seleted ] } }
    def write_cart_to_redis(self,user_id,cart_dict):
        redis_conn = get_redis_connection('cart')
        key = "cart_%s" % user_id
        cart_bytes = pickle.dumps(cart_dict)
        redis_conn.set(key,cart_bytes)


    def write_cart_to_cookie(self,cart_dict, response):
        for operate in self.encoder:
            cart_dict = operate(cart_dict)
        response.set_cookie('cart', value=cart_dict, max_age=constants.CART_COOKIE_EXPIRES)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        request.cart = self.read_cart(request)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        self.write_cart(request, request.cart , response)
        return response


def merge_cart_cookie_to_redis(request, user, response:Response):
    """登录合并购物车"""
    cart_obj = CartMixin()
    # redis cart (base)
    redis_cart = cart_obj.read_cart_from_redis(user.id)
    # cookie cart
    cookie_cart = cart_obj.read_cart_from_cookie(request)
    # merge cart
    redis_cart.update(cookie_cart)
    # save cart info to redis
    cart_obj.write_cart_to_redis(user.id, redis_cart)
    # delete cookie cart
    response.delete_cookie('cart')


def after_login(func):
    def wrapper(request,*args,**kwargs):
        response = func(request,*args,**kwargs) # type:Response
        if response.status_code >= 200 and response.status_code < 300:
                merge_cart_cookie_to_redis(request, request.user, response)
        return response
    return wrapper