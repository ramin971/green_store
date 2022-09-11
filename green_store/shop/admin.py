from django.contrib import admin
from .models import Profile,Attribute,Category,Product,Comment,Rating,Coupon,ProductImage,Variation,Basket,OrderItem
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

class ProductImageInline(admin.StackedInline):
    model = ProductImage
    extra = 1

class VariationInline(admin.StackedInline):
    model = Variation
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
    list_display = ['name','category',new_price,avg_rate,'stock','get_attribute','discount','price','created']
    list_filter = ['category','created','price']
    search_fields = ['name','attribute__value']
    inlines = [ProductImageInline,VariationInline]
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
    # list_display = ['name','slug','parent']

class CommentAdmin(admin.ModelAdmin):
    list_display = ['pk','user','product','show']

class RatingAdmin(admin.ModelAdmin):
    list_display =['pk','user','product','rate']

class VariationAdmin(admin.ModelAdmin):
    list_display = ['product','get_privileged_att','price','stock','created']
    search_fields = ['product__name','privileged_attribute__value']
    list_filter = ['product__category','created','price']


class BasketAdmin(admin.ModelAdmin):
    list_display = ['user','get_order_items','ordered_date','coupon','payment','status','get_total_price']
    readonly_fields = ['user','tracking_code','get_total_price','payment','coupon','ordered_date']
    search_fields = ['user','tracking_code']
    list_filter = ['status','ordered_date']

    # Function to filter and display just Basket object that payment=True/
    def get_queryset(self, request):
        qs = super(BasketAdmin, self).get_queryset(request)
        return qs.filter(payment=True)



admin.site.register(Profile,ProfileAdmin)
admin.site.register(Attribute)
admin.site.register(Rating,RatingAdmin)
admin.site.register(Comment,CommentAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(Product,ProductAdmin)
admin.site.register(Variation,VariationAdmin)
admin.site.register(ProductImage)
admin.site.register(Coupon)
admin.site.register(Basket,BasketAdmin)
admin.site.register(OrderItem)