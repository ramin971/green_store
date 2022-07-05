from django.contrib import admin
from .models import Profile,Attribute,Category,Product,Comment,Rating
from django.db.models import Avg,Sum
# Register your models here.

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user','email','postal_code','phone']
    search_fields = ['phone','user__username']

def avg_rate(obj):
    this_product=obj.rates.aggregate(avg=Avg('rate'))
    return this_product['avg']

def new_price(obj):
    old_price=obj.price
    discount=obj.discount
    if discount is not None:
        print('>>>>>>>>>>is not non')
        new_price = old_price - (discount * old_price // 100)
        return new_price


class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
    list_display = ['name','category',new_price,avg_rate,'stock','get_attribute','discount','price','created']
    list_filter = ['category','created','price']
    search_fields = ['name','color']

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
    # list_display = ['name','slug','parent']

class CommentAdmin(admin.ModelAdmin):
    list_display = ['pk','user','product','show']

class RatingAdmin(admin.ModelAdmin):
    list_display =['pk','user','product','rate']

admin.site.register(Profile,ProfileAdmin)
admin.site.register(Attribute)
admin.site.register(Rating,RatingAdmin)
admin.site.register(Comment,CommentAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(Product,ProductAdmin)