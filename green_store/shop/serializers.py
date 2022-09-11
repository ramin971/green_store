from rest_framework import serializers
from .models import Product,Profile,Comment,Category,Attribute,Rating,Variation,Basket,ProductImage,Coupon,OrderItem
from django.contrib.auth.models import User
from django.db.models import Avg,Sum,F
from django.contrib.auth.password_validation import validate_password
from rest_framework.pagination import PageNumberPagination


class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['id','username','password']
        extra_kwargs={'id':{'read_only':True},'password':{'write_only':True}}
    def validate_password(self,value):
        print('value',value)
        validate_password(value)
        return value
    def create(self, validated_data):
        username=validated_data['username']
        password=validated_data['password']
        user=User.objects.create_user(username=username,password=password)
        return user

class ChangePasswordSerializers(serializers.Serializer):
    old_password=serializers.CharField(required=True,write_only=True)
    new_password=serializers.CharField(required=True,write_only=True)

    def validate_new_password(self,value):
        validate_password(value)
        print('valid new pass')
        return value

    def validate_old_password(self,value):
        print("context",self.context)
        user = self.context['request'].user
        print(user)
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Your old password was entered incorrectly. Please enter it again.'
            )
        return value
    def save(self, **kwargs):
        password=self.validated_data['new_password']
        user=self.context['request'].user
        user.set_password(password)
        user.save()
        return user


class CategorySerializers(serializers.ModelSerializer):
    parent_name=serializers.SerializerMethodField()
    class Meta:
        model=Category
        fields=['id','name','parent','parent_name']

    def get_parent_name(self,obj):
        parent=[]
        temp=obj.parent
        while temp is not None:
            parent.append(temp.name)
            temp=temp.parent
        return parent
        # return obj.__str__()

class ProfileSerializers(serializers.ModelSerializer):
    # user=UserSerializers(read_only=True)
    class Meta:
        model=Profile
        # fields=['id','f_name','l_name','address','email','postal_code','phone','created','user']
        fields='__all__'
        extra_kwargs = {"user": {"read_only": True},"id":{"read_only":True}}


class AttributeSerializers(serializers.ModelSerializer):
    class Meta:
        model=Attribute
        fields=['id','name','value']


class CommentSerializers(serializers.ModelSerializer):
    class Meta:
        model=Comment
        fields='__all__'
        extra_kwargs={"user":{"read_only":True},"product":{"read_only":True},"show":{"read_only":True}}

class RatingSerializers(serializers.ModelSerializer):
    class Meta:
        model=Rating
        # fields='__all__'   -->  product , user ro mikhad ba inke to view joda dadim pass nemidim inja behesh
        fields=['id','rate']


class ProductImageSerializers(serializers.ModelSerializer):
    class Meta:
        model=ProductImage
        fields=['id','product_id','images']

class ProductSerializers(serializers.ModelSerializer):
    rate=serializers.SerializerMethodField()
    new_price=serializers.SerializerMethodField()
    images=serializers.SerializerMethodField()
    class Meta:
        model=Product
        fields=['id','name','images','price','description','stock',
                'created','rate','discount','new_price']
        extra_kwargs={"new_price":{"read_only":True},"description":{"write_only":True}}

    #
    # def create(self, validated_data):
    #     images_data = self.context.get('view').request.FILES
    #     name=validated_data.get('name')
    #     price=validated_data.get('price')
    #     description=validated_data.get('description')
    #     stock=validated_data.get('stock')
    #     discount=validated_data.get('discount')
    #     product = Product.objects.create(name=name,price=price,description=description,stock=stock,discount=discount,)
    #     for image_data in images_data.values():
    #         ProductImage.objects.create(product=product, image=image_data)
    #     return product


    def get_images(self,obj):
        image=obj.images.values().first()
        # image=list(obj.images.values_list(flat=True))
        return image

    def get_rate(self,obj):
        this_product = obj.rates.aggregate(avg=Avg('rate'))
        return this_product['avg']

    def get_new_price(self,obj):
        old_price = obj.price
        discount = obj.discount
        if discount is not None:
            new_price = old_price - (discount * old_price // 100)
            return new_price

class VariationsSerializers(serializers.ModelSerializer):
    privileged_attribute=AttributeSerializers(many=True,read_only=True)

    class Meta:
        model=Variation
        fields=['id','product_id','price','stock','created','privileged_attribute']



class ProductDetailSerializers(serializers.ModelSerializer):
    rate=serializers.SerializerMethodField()
    # comments=serializers.SerializerMethodField()
    images=serializers.SerializerMethodField()
    new_price=serializers.SerializerMethodField()
    variations=VariationsSerializers(many=True,read_only=True)
    attribute=AttributeSerializers(many=True,read_only=True)

    class Meta:
        model=Product
        fields=['id','name','images','price','discount','new_price','rate','stock',
                'created','description','attribute','variations']

        read_only_fields = ['id', 'name', 'images', 'price', 'discount', 'new_price', 'rate', 'stock',
                  'created', 'description', 'attribute', 'variations']

    def get_images(self,obj):
        image=obj.images.values()
        return image

    def get_rate(self,obj):
        avg_rate=obj.rates.aggregate(avg=Avg('rate'))
        return avg_rate['avg']

    # def get_comments(self,obj):
    #     comments=obj.comments.filter(show=True).values()
    #     paginator = PageNumberPagination()
    #     paginator.page_size = 3
    #
    #     serializer=CommentSerializers(comments,many=True,context={'request': self.context['request']})
    #     result_page = paginator.paginate_queryset(serializer.data,self.context['request'] )
    #     return result_page

    #     # ^ or ->
        # result_page = paginator.paginate_queryset(comments,self.context['request'] )
        # serializer=CommentSerializers(result_page,many=True)
        # return serializer.data

    def get_new_price(self,obj):
        old_price = obj.price
        discount = obj.discount
        if discount:
            new_price = old_price - (discount * old_price // 100)
            return new_price


class OrderItemSerializers(serializers.ModelSerializer):
    user=UserSerializers(read_only=True)
    product=ProductSerializers(read_only=True)
    variation=VariationsSerializers(read_only=True)
    # total=serializers.SerializerMethodField()
    class Meta:
        model=OrderItem
        fields=['id','user','product','quantity','variation','get_total_product_price']
        read_only_field=['__all__']
    # def get_total(self,obj):
    #     if obj.variation:
    #         return obj.quantity * obj.variation.price
    #     elif obj.product.discount:
    #         old_price = obj.product.price
    #         discount = obj.product.discount
    #         new_price = old_price - (discount * old_price // 100)
    #         return obj.quantity * new_price
    #     else:
    #         return obj.quantity * obj.product.price

class BasketSerializers(serializers.ModelSerializer):
    user=UserSerializers(read_only=True)
    order_items=OrderItemSerializers(many=True)
    # total_price=serializers.SerializerMethodField()
    class Meta:
        model = Basket
        fields=['id','user','order_items','ordered_date','coupon','payment','status','get_total_price']
        read_only_fields=['id','user','payment','provider_order','send_order','get_total_price']
    #
    # def get_total_price(self,obj):

    #     # total=obj.values('order_items').aggregate(total_price=Sum(F('product__price') * 0.01 * (100 - F('product__discount'))))['total_price']
    #     # total=obj.order_items.values('product').aggregate(total_price=Sum(F('product__price') * 0.01 * (100 - F('product__discount'))*F('quantity')))['total_price']
    #
    #
    #     if obj.order_items.variation.first():
    #     total=obj.order_items.values('product').aggregate(total_price=Sum(F('product__price') * 0.01 * (100 - F('product__discount'))*F('quantity')))['total_price']
    #     return total