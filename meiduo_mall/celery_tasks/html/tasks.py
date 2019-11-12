import os

from django.conf import settings
from django.template import loader

from celery_tasks.main import celery_app
from contents.crons import get_categories
from goods.utils import get_sku_detail


def generate_static_sku_detail(sku_id):
    """
       生成静态商品详情页面
       :param sku_id: 商品sku id
    """
    # 商品分类菜单
    categories = get_categories()

    # 获取当前SKU的详情信息
    context = get_sku_detail(sku_id)

    # 渲染模板，生成静态html文件
    context['categories'] = categories

    template = loader.get_template('detail.html')
    html_text = template.render(context)
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'goods/' + str(sku_id) + '.html')
    with open(file_path, 'w') as f:
        f.write(html_text)

generate_static_sku_detail_html = celery_app.task(name='generate_static_sku_detail_html')(generate_static_sku_detail)



