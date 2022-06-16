import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly,AllowAny
from .serializers import UserSerializers,ProductSerializers,CategorySerializers,\
    ProfileSerializers,AttributeSerializers,CommentSerializers,RatingSerializers
from .models import Product,Profile,Comment,Category,Attribute,Rating
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


# Create your views here.

def token_expire_handler(token):
    print('#############timezone.now: ',timezone.now())
    print('#############token_created: ',token.created)
    time_elapsed = timezone.now() - token.created
    left_time = timedelta(seconds = settings.TOKEN_EXPIRED_AFTER_SECONDS) - time_elapsed
    print('##########left_time= ',left_time)
    print('##########expired= ',left_time < timedelta(seconds=0))
    is_token_expired=left_time < timedelta(seconds=0)
    if is_token_expired:
        token.delete()
        raise AuthenticationFailed('token expired')

    if not token.user.is_active:
        raise AuthenticationFailed('User inactive or deleted')

    return left_time

@api_view(['POST'])
@permission_classes((AllowAny,))
def register(request):
    serializer=UserSerializers(data=request.data)
    if serializer.is_valid():
        user=serializer.save()
        token=Token.objects.create(user=user)
        result={
            'username':serializer.data['username'],
            'token':token.key
        }
        return Response(result,status=status.HTTP_201_CREATED)
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST','PUT'])
def profile(request):
    try:
        user=request.user
        print(user)
    except User.DoesNotExist:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    # Check token Expire:
    token_expire_handler(token=request.auth)

    if request.method=='GET':
        if Profile.objects.filter(user=user).exists():
            profile=Profile.objects.get(user=user)
            serializer=ProfileSerializers(profile)
            res=serializer.data
            res['username']=user.username
            return Response(res,status=status.HTTP_200_OK)
        else:
            res={
                'error':'profile is not exist for current user.please complete profile.'
            }
            return Response(res,status=status.HTTP_404_NOT_FOUND)

    if request.method=='POST':
        profile=Profile(user=user)
        serializer=ProfileSerializers(profile,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_started(request):
    # new_product=
    # off_prduct=
    # new_off=new_product+off_prduct #inoo chejory append konam queryclass bashe?
    # serializer=ProductSerializer()
    pass


@api_view(['GET','POST','DELETE'])
@permission_classes((IsAuthenticatedOrReadOnly,))
def category(request):
    if request.method=='GET':
        all_category=Category.objects.all()
        serializer=CategorySerializers(all_category,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    elif request.method=='POST':
        user=request.user
        if user.is_superuser:
            # Check token expire
            token_expire_handler(token=request.auth)

            serializer = CategorySerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            res = {
                'error': 'permission denied.you not superuser'
            }
            return Response(res, status=status.HTTP_400_BAD_REQUEST)

    elif request.method=='DELETE':
        # Check token expire
        token_expire_handler(token=request.auth)

        try:
            temp_obj=Category.objects.get(id=request.data['id'])
        except Category.DoesNotExist:
            res={
                'error':'category with this ID does not exist'
            }
            return Response(res,status=status.HTTP_404_NOT_FOUND)
        user=request.user
        if user.is_superuser:
            temp_obj.delete()
            res={
                'message':'category deleted'
            }
            return Response(res,status=status.HTTP_204_NO_CONTENT)
        res={
            'error':'permission denied.you not superuser'
        }
        return Response(res,status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST','DELETE'])
def attribute(request):
    # if request.method=='GET':
    #     all_attribute=Attribute.objects.all()
    #     serializer=AttributeSerializers(all_attribute,many=True)
    #     return Response(serializer.data,status=status.HTTP_200_OK)

    if request.method=='POST':
        user=request.user
        if user.is_superuser:
            token_expire_handler(token=request.auth)
            serializer = AttributeSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_201_CREATED)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        res = {
            'error': 'permission denied.you are not superuser'
        }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

    elif request.method=='DELETE':
        user=request.user
        if user.is_superuser:
            token_expire_handler(token=request.auth)
            try:
                temp_obj=Attribute.objects.get(id=request.data['id'])
            except Attribute.DoesNotExist:
                res = {
                    'error': 'attribute with this ID does not exist'
                }
                return Response(res, status=status.HTTP_404_NOT_FOUND)
            temp_obj.delete()
            res = {
                'message': 'attribute deleted'
            }
            return Response(res, status=status.HTTP_204_NO_CONTENT)
        res = {
            'error': 'permission denied.you are not superuser'
        }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST','DELETE'])
def comment(request):
    if request.method=='POST':
        try:
            product=Product.objects.get(id=request.data['product_id'])
        except Product.DoesNotExist:
            res = {
                'error': 'product with this ID does not exist'
            }
            return Response(res,status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        temp_comment=Comment(product=product,user=user)
        serializer = CommentSerializers(temp_comment,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    elif request.method=='DELETE':
        user=request.user
        if user.is_superuser:
            token_expire_handler(token=request.auth)
            try:
                temp_obj=Comment.objects.get(id=request.data['comment_id'])
            except Attribute.DoesNotExist:
                res = {
                    'error': 'comment with this ID does not exist'
                }
                return Response(res, status=status.HTTP_404_NOT_FOUND)
            temp_obj.delete()
            res = {
                'message': 'comment deleted'
            }
            return Response(res, status=status.HTTP_204_NO_CONTENT)
        res = {
            'error': 'permission denied.you are not superuser'
        }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST',])
@permission_classes((AllowAny,))
def rating(request):
    if request.method=='POST':
        try:
            product=Product.objects.get(id=request.data['product_id'])
        except Product.DoesNotExist:
            res = {
                'error': 'product with this ID does not exist'
            }
            return Response(res, status=status.HTTP_400_BAD_REQUEST)
        user=request.user
        token_expire_handler(token=request.auth)
        old_rate=Rating.objects.filter(user=user,product=product)
        if old_rate.exists():
            old_rate.delete()
        temp_rating=Rating(user=user,product=product)
        serializer=RatingSerializers(temp_rating,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','POST'])
@permission_classes((AllowAny,))
# @permission_classes((IsAuthenticatedOrReadOnly,))
def products(request):
    if request.method=='GET':
        try:
            all_product=Product.objects.all()
        except Product.DoesNotExist:
            res = {
                'error': 'any product does not exist'
            }
            return Response(res, status=status.HTTP_400_BAD_REQUEST)
        serializer=ProductSerializers(all_product,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    elif request.method=='POST':
        user=request.user
        if user.is_superuser:
            # token_expire_handler(token=request.auth)

            temp_category=Category.objects.get(slug=request.data['category'])
            att=request.data['attribute']
            json_att=json.loads(att)
            print(json_att)
            print(type(json_att))
            print('att: ',att)
            print('type att: ',type(att))
            names=[]
            values=[]
            # (names.append(i['name']) for i in att if not i['name'] in names)
            for i in json_att:
                print('for i in att ->i :****',i)
                # print('for i in att ->i[name]:****',i['name'])
                # print('for i in att ->i[value] :****',i['value'])

                # if not i['name'] in names:
                if not i.get('name') in names:
                    print(i['name'])
                    names.append(i['name'])
                if not i['value'] in values:
                    print(i['value'])
                    values.append(i['value'])

            print('values@@@@@@@@@@@@@@',values)
            print('names:$$$$$$$$$$',names)

            temp_attribute=Attribute.objects.filter(name__in=names,value__in=values)
            product=Product(category=temp_category)
            serializer = ProductSerializers(product,data=request.data)
            if serializer.is_valid():
                serializer.save()
                # final_attribute=[]
                for i in temp_attribute:
                    print('attribute:############', i)
                    product.attribute.add(i)
                    # temp='{}({})'.format(i.name,i.value)
                    # final_attribute.append(temp)
                # print('final_attribute:#########',final_attribute)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        res = {
                'error': 'permission denied.you are not superuser'
            }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

            # posted_attribute_name_list=request.data['names'].split(',')
            # temp_attribute=Attribute.objects.filter(name__in=posted_attribute_name_list)
            # product=Product(category=temp_category)
            # # product=Product(category=temp_category,attribute=temp_attribute)
            # serializer = ProductSerializers(product,data=request.data)
            # if serializer.is_valid():
            #     serializer.save()
            #     att=[]
            #     for i in temp_attribute:
            #         print('attribute:############', i)
            #         product.attribute.add(i)
            #         temp='{}({})'.format(i.name,i.value)
            #         att.append(temp)
            #     print('#########',att)
            #     res=serializer.data
            #     res['attribute']=att


        #         return Response(res, status=status.HTTP_201_CREATED)
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # res = {
        #     'error': 'permission denied.you are not superuser'
        # }
        # return Response(res, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','PUT','DELETE'])
def product_details(request):
    pass