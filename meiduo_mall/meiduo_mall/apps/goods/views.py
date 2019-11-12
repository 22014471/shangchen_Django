import json

from django.shortcuts import render
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from goods.models import SKU, GoodsCategory, GoodsChannel
from goods.serializers import SKUIndexSerializer
from meiduo_mall.utils.pagination import StandardResultsSetPagination
from users.serializers import SKUSerializer


# GET /categories/(?P<category_id>\d+)/skus?page=xxx&page_size=xxx&ordering=xxx
class SKUListView(ListAPIView):
    """
    sku列表数据
    """
    # 序列化器用于序列化输出
    serializer_class = SKUSerializer

    # 分页：构建一个类，其继承于PageNumberPagination，用于标准化分页
    pagination_class = StandardResultsSetPagination
    # 排序：drf有专门的排序工具类 OrderingFilter，通过ordering_fields来说明哪些是排序字段
    filter_backends = [OrderingFilter]
    # 返回值:ListAPIView已完成
    ordering_fields = ('create_time', 'price', 'sales')

    # query_set:通过category_id获取当前三级类别列表,不能使用类属性（无法通过路径参数获取category_id）
    def get_queryset(self):
        category_id = self.kwargs['category_id']
        return SKU.objects.filter(category_id = category_id, is_launched=True)


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]
    serializer_class = SKUIndexSerializer

# GET categories/(?P<category_id>\d+)/
class SKUCategoriesView(APIView):
    """获取商品具体分类的展示"""
    def get(self,request, category_id):
        try:
            goodscategory = GoodsCategory.objects.filter(id=category_id)[0]
        except GoodsCategory.DoesNotExist:
            raise Exception('您所查的数据存在错误！')
        cat3 = goodscategory
        cat2 = cat3.parent
        cat1 = cat2.parent
        goodschannel = GoodsChannel.objects.get(id=cat1.id)
        if not all([cat1,cat2,cat3]):
            raise Exception('您所查的数据存在错误！')
        data = {
            'cat1': {'url': goodschannel.url, 'category':{'name': cat1.name, 'id': cat1.id}},
            'cat2': {"name":cat2.name},
            'cat3': {"name":cat3.name},
        }
        print(data)
        return Response(data=data)


