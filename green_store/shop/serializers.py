from rest_framework import serializers
from .models import Product,Profile,Comment,Category,Attribute,Rating
from django.contrib.auth.models import User


class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['id','username','password']
        extra_kwargs={'id':{'read_only':True},'password':{'write_only':True}}
    def create(self, validated_data):
        username=validated_data['username']
        password=validated_data['password']
        user=User.objects.create_user(username=username,password=password)
        return user

class ProductSerializers(serializers.ModelSerializer):
    class Meta:
        model=Product
        # fields=['id','name','image','attribute','price','slug','category','description','stock','created']
        fields='__all__'

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