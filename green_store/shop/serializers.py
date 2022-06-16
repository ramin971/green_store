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
    attribute_names=serializers.SerializerMethodField()
    class Meta:
        model=Product
        fields=['id','name','image','price','description','stock','created','attribute_names']
        # fields='__all__'
#         exclude category and attribute
    def get_attribute_names(self, obj):
        # return obj.get_attribute
        attributes=[]
        for i in obj.attribute.all():
            temp='{}({})'.format(i.name,i.value)
            attributes.append(temp)
        return attributes

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