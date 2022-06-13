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
# def avg_rate(obj):
#     this_product=obj.rates.values_list('rate',flat=True)
#     k=obj.rates.aggregate(sum=Sum('rate'))
#     print(k['sum']/len(this_product))

    # l=0
    # for i in this_product:
    #     l=l+i
    # print('average=',l/len(this_product))
    # print(this_product)
    # return this_product['avg']


class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
    list_display = ['name','category','price',avg_rate,'stock','get_attribute','created']
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