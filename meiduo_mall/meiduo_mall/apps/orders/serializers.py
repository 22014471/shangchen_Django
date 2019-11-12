import pickle
from decimal import Decimal
import logging

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django_redis import get_redis_connection
from rest_framework import serializers

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods

logger = logging.getLogger('django')

class CartSKUSerializer(serializers.ModelSerializer):
    """
    购物车商品数据序列化器
    """
    count = serializers.IntegerField(label='数量')

    class Meta:
        model = SKU
        fields = ('id', 'name', 'default_image_url', 'price', 'count')


class OrderSettlementSerializer(serializers.Serializer):
    """
    订单结算数据序列化器
    """
    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)


class SaveOrderSerializer(serializers.ModelSerializer):
    """
    下单数据序列化器
    """
    class Meta:
        model = OrderInfo
        fields = ('order_id', 'address', 'pay_method')
        read_only_fields = ('order_id',)
        extra_kwargs = {
            'address': {
                'write_only': True,
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True
            }
        }

    def create(self, validated_data):
        """保存订单"""
        address = validated_data['address']
        pay_method = validated_data['pay_method']
        # 获取当前下单用户
        user = self.context['request'].user
        # 从redis中查询购物车  sku_id  count  selected
        # redis   string  {cart_user_id : {sku_id1:[ count, seleted ],sku_id2:[ count, seleted ] } }
        redis_conn = get_redis_connection('cart')
        key = "cart_%s" % user.id
        cart_bytes = redis_conn.get(key)
        cart = pickle.loads(cart_bytes)

        if not cart:
            raise serializers.ValidationError('没有需要结算的商品')
        # 创建事务 开启一个事务
        with transaction.atomic():
            try:
                # 创建保存点
                save_id = transaction.savepoint()
                # 保存订单
                # 生成订单编号order_id
                # 20180702150101  9位用户id
                # datetime -> str   strftime
                #  str -> datetime  strptime
                order_id = timezone.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
                # 创建订单基本信息表记录 OrderInfo
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM[
                        'CASH'] else OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                )
                # 查询商品数据库，获取商品数据（库存）
                sku_id_list = []
                for sku_id in cart.keys():
                    if cart[sku_id][1] == True:
                        sku_id_list.append(int(sku_id))
                # sku_obj_list = SKU.objects.filter(id__in=sku_id_list)
                # 遍历需要结算的商品数据
                for sku_id in sku_id_list:
                    # 用户需要购买的数量
                    sku_count = cart[str(sku_id)][0]

                    while True:
                        # 查询商品的最新库存信息
                        sku = SKU.objects.get(id=sku_id)
                        # 库存减少 销量增加
                        # update返回受影响的行数   ----> 　使用了乐观锁；　事务隔离级别：已提交读（Read committed）
                        result = SKU.objects.filter(id=sku.id, stock__gte=sku_count).update(stock=F("stock")-sku_count, sales=F("sales")+sku_count)
                        if result == 0:
                            # 表示更新失败，有人抢了商品
                            # 结束本次while循环，进行下一次while循环
                            continue
                        # sku.save()
                        order.total_count += sku_count
                        order.total_amount += (sku.price * sku_count)
                        # 创建订单商品信息表记录 OrderGoods
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price,
                        )
                        # 跳出while循环，进行for循环
                        break
                order.save()
            # except serializers.ValidationError:
            #     raise
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)
                raise
            else:
                transaction.savepoint_commit(save_id)
        # 删除购物车中已结算的商品
        for sku_id in sku_id_list:
            cart.pop(str(sku_id))
        cart_bytes = pickle.dumps(cart)
        redis_conn.set(key, cart_bytes)
        # 返回OrderInfo对象
        return order
