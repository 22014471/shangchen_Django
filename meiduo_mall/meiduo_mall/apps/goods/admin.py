from django.contrib import admin
from . import models

# Register your models here.


from django.contrib import admin
from . import models
class SKUAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.id)
class SKUSpecificationAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)
    def delete_model(self, request, obj):
        sku_id = obj.sku.id
        obj.delete()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)
class SKUImageAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # obj -> SKUImage 对象  obj.sku

        obj.save()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(obj.sku.id)

        # 设置SKU默认图片
        sku = obj.sku
        if not sku.default_image_url:
            # http://image.meiduo.site:8888/groupxxxxxx
            sku.default_image_url = obj.image.url
            sku.save()

    def delete_model(self, request, obj):
        sku_id = obj.sku.id
        obj.delete()
        from celery_tasks.html.tasks import generate_static_sku_detail_html
        generate_static_sku_detail_html.delay(sku_id)

admin.site.register(models.GoodsCategory)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU, SKUAdmin)
admin.site.register(models.SKUSpecification, SKUSpecificationAdmin)
admin.site.register(models.SKUImage, SKUImageAdmin)