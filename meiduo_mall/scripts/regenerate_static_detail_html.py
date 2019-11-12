#!/usr/bin/env python
"""
功能：手动生成所有SKU的静态detail html文件
使用方法:
    ./regenerate_detail_html.py
"""
import sys



sys.path.insert(0, '../')
import os
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'meiduo_mall.settings.dev'
import django
django.setup()

from goods.models import SKU

from celery_tasks.html.tasks import generate_static_sku_detail_html

if __name__ == '__main__':
    skus = SKU.objects.all()
    for sku in skus:
        print(sku.id)
        generate_static_sku_detail_html(sku.id)