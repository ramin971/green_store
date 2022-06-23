from rest_framework import serializers
from .models import Product,Profile,Comment,Category,Attribute,Rating
from django.contrib.auth.models import User
from django.db.models import Avg,Sum
from django.contrib.auth.password_validation import validate_password


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

#
# class ProductSerializers(serializers.ModelSerializer):
#     attribute_names=serializers.SerializerMethodField()
#     class Meta:
#         model=Product
#         fields=['id','name','image','price','description','stock','created','attribute_names']
#         # fields='__all__'
# #         exclude category and attribute
#     def get_attribute_names(self, obj):
#         # return obj.get_attribute
#         attributes=[]
#         for i in obj.attribute.all():
#             temp='{}({})'.format(i.name,i.value)
#             attributes.append(temp)
#         return attributes



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
    class Meta:
        model=Profile
        # fields='__all__'
        exclude=('user',)

class AttributeSerializers(serializers.ModelSerializer):
    class Meta:
        model=Attribute
        fields=['id','name','value']

class CommentSerializers(serializers.ModelSerializer):
    class Meta:
        model=Comment
        # fields=[]
        exclude=('user','product')

class RatingSerializers(serializers.ModelSerializer):
    class Meta:
        model=Rating
        # fields='__all__'   -->  product , user ro mikhad ba inke to view joda dadim pass nemidim inja behesh
        fields=['id','rate']

class ProductSerializers(serializers.ModelSerializer):
    # attribute_names=serializers.SerializerMethodField()
    rate=serializers.SerializerMethodField()
    # attribute=AttributeSerializers(many=True,read_only=True)
    class Meta:
        model=Product
        fields=['id','name','image','price','description','stock','created','rate']

        # fields='__all__'
#         exclude category and attribute
#     def get_attribute_names(self, obj):
#         # return obj.get_attribute
#         attributes=[]
#         for i in obj.attribute.all():
#             temp='{}({})'.format(i.name,i.value)
#             attributes.append(temp)
#         return attributes
    def get_rate(self,obj):
        this_product = obj.rates.aggregate(avg=Avg('rate'))
        return this_product['avg']

class ProductDetailSerializers(serializers.ModelSerializer):
    rate=serializers.SerializerMethodField()
    # comments=CommentSerializers(many=True,read_only=True)
    comments=serializers.SerializerMethodField()
    attribute=AttributeSerializers(many=True,read_only=True)
    class Meta:
        model=Product
        fields=['id','name','image','price','description','stock','created','attribute','rate','comments']

    def get_rate(self,obj):
        avg_rate=obj.rates.aggregate(avg=Avg('rate'))
        return avg_rate['avg']

    def get_comments(self,obj):
        comments=obj.comments.filter(show=True).values()
        return comments