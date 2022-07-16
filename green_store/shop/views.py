from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny
from .serializers import UserSerializers,ProductSerializers,CategorySerializers,\
    ProfileSerializers,AttributeSerializers,CommentSerializers,RatingSerializers,ProductDetailSerializers,ChangePasswordSerializers
from .models import Product,Profile,Comment,Category,Attribute,Rating
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import json
from itertools import chain

# Create your views here.

def token_expire_handler(token):
    # print('#############timezone.now: ',timezone.now())
    # print('#############token_created: ',token.created)
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

@api_view(['PUT'])
def change_password(request):

    # Check token Expire:
    token_expire_handler(token=request.auth)
    serializer=ChangePasswordSerializers(data=request.data,context={'request':request})

    if serializer.is_valid():
        serializer.save()

        res={
            'message': 'Your Password Update Successfully'
        }
        return Response(res,status=status.HTTP_200_OK)
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout(request):
    user=request.user
    user_token=request.auth
    if user_token:
        user_token.delete()
        message='Dear {}, You logout successfully and your Token deleted'.format(user)
        res={
            'message': message
        }
        return Response(res,status=status.HTTP_200_OK)
@api_view(['GET','POST','PUT'])
def profile(request):
    try:
        user=request.user
    except User.DoesNotExist:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    # Check token Expire:
    token_expire_handler(token=request.auth)

    if request.method=='GET':
        if Profile.objects.filter(user=user).exists():
            profile=Profile.objects.get(user=user)
            serializer=ProfileSerializers(profile)
            res=serializer.data
            res['user_id']=user.id
            res['username']=user.username
            res.pop('user')
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
                'error': 'Permission denied. You are not SuperUser'
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
            'error':'Permission denied. You are not SuperUser'
        }
        return Response(res,status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','POST','DELETE'])
@permission_classes((IsAuthenticatedOrReadOnly,))
def attribute(request):
    if request.method=='GET':
        all_attribute=Attribute.objects.all()
        serializer=AttributeSerializers(all_attribute,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

    if request.method=='POST':
        user=request.user
        if user.is_superuser:
            # Check token expire
            token_expire_handler(token=request.auth)
            serializer = AttributeSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_201_CREATED)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        res = {
            'error': 'Permission denied. You are not SuperUser'
        }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

    elif request.method=='DELETE':
        user=request.user
        if user.is_superuser:
            # Check token expire
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
            'error': 'Permission denied. You are not SuperUser'
        }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST','DELETE'])
def comment(request):
    if request.method=='POST':
        try:
            product=Product.objects.get(slug=request.data['product_slug'])
        except Product.DoesNotExist:
            res = {
                'error': 'product with this Slug does not exist'
            }
            return Response(res,status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        # Check token expire
        token_expire_handler(token=request.auth)
        temp_comment=Comment(product=product,user=user)
        serializer = CommentSerializers(temp_comment,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    elif request.method=='DELETE':
        user=request.user
        if user.is_superuser:
            # Check token expire
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
            'error': 'Permission denied. You are not SuperUser'
        }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((AllowAny,))
def rating(request):
    if request.method=='POST':
        try:
            product=Product.objects.get(slug=request.data['product_slug'])
        except Product.DoesNotExist:
            res = {
                'error': 'product with this Slug does not exist'
            }
            return Response(res, status=status.HTTP_400_BAD_REQUEST)
        user=request.user
        # Check token expire
        token_expire_handler(token=request.auth)
        old_rate=Rating.objects.filter(user=user,product=product)
        # remove old rate if a user rates twice to product
        if old_rate.exists():
            old_rate.delete()
        temp_rating=Rating(user=user,product=product)
        serializer=RatingSerializers(temp_rating,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def add_product(request):
    if request.method=='POST':
        user=request.user
        if user.is_superuser:
            # Check token expire
            token_expire_handler(token=request.auth)

            temp_category=Category.objects.get(slug=request.data['category_slug'])
            att=request.data['attribute']
            json_att=json.loads(att)
            names=[]
            values=[]
            # get the desired attributes
            for i in json_att:
                if not i.get('name') in names:
                    # print(i['name'])
                    names.append(i['name'])
                if not i['value'] in values:
                    # print(i['value'])
                    values.append(i['value'])

            temp_attribute=Attribute.objects.filter(name__in=names,value__in=values)
            product=Product(category=temp_category)
            serializer = ProductSerializers(product,data=request.data)
            if serializer.is_valid():
                serializer.save()
                for i in temp_attribute:
                    # print('attribute:############', i)
                    product.attribute.add(i)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        res = {
                'error': 'Permission denied. You are not SuperUser'
            }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
def products_by_category(request,category_slug):
    if request.method=='GET':
        try:
            # Product.objects.filter(sto)
            products=Product.objects.filter(category__slug=category_slug)
        except Product.DoesNotExist:
            res = {
                'error': 'any product does not exist'
            }
            return Response(res, status=status.HTTP_400_BAD_REQUEST)

    # Search-Filter
        qp=request.query_params.copy()
        discount=qp.get('discount')
        stock=qp.get('stock')
        max_price=qp.get('maxprice')
        min_price=qp.get('minprice')

        if (max_price and min_price):
            products=products.filter(price__range=(min_price,max_price))
            qp.pop('maxprice')
            qp.pop('minprice')
        print('qp after maxmin=',qp)

        if discount:
            if discount == '1':
                products=products.filter(discount__isnull=False)
            qp.pop('discount')
        print('qp after discount=',qp)

        if stock:
            if stock == '1':
                products=products.filter(stock__gt=0)
            qp.pop('stock')
        print('qp after stock=',qp)
        print('qp key=',qp.keys())
        print('qp value=',qp.values())
        names=qp.keys()
        values=[]

        for item in qp:
            for value in qp.getlist(item):
                print('value',value)
                values.append(value)

        temp_att=Attribute.objects.filter(name__in=names,value__in=values)
        print(temp_att)

        if temp_att.exists():
            products=products.filter(attribute__in=temp_att)
    # end Search-Filter
    # Ordering


            # att=Attribute.objects.filter(name)
            # if item in temp_att:
        # if att is not None:
        #     # products=product.filter(attribute__in=temp_att  or --> att__name__in=att.items.keys()
        #
        #     pass

        # for i in request.query_params:
        #     print(i)
        #     if i=='discount':
        #         if discount=='1':
        #             print('11111')
        #             products=products.filter(discount__isnull=False)
        #             print(products)
        #
        #     elif i=='stock':
        #         if stock=='1':
        #             print('11111')
        #             products=products.filter(stock__gt=1)
        #             print(products)
        #
        #     elif i=='att':
        #         pass
        #     elif i=='price':
        #
        #         pass
        # a=request.GET.dict().copy()
        # b=request.query_params.copy()
        # b.pop('discount')
        # # request.GET.dict().pop(discount)
        # c=request.query_params.pop('stock')
        # request.query_params.get(discount)
        # print('req.g.dict.all#########',request.GET.dict())
        # # print('req.g.dict.all-discount#########',request.GET.dict().pop(discount))
        # # print('req.g.dict.all-discount#########',a.pop(discount))
        # print('query_params.all#########',request.query_params)
        # print('query_params.all.copy-stock#########',b)
        # print('query_params.all#########',request.query_params)
        # print('query_params.all-stock#########',c)
        # print('query_params.all#########',request.query_params)
        # # print('query_params.all-stock#########',b.pop(stock))
        # print('query_params.all#########',request.GET.urlencode())
        # print('timedelta:',timedelta(days=43))
        # print('GET.query_params#########',request)
        # print('GET.query_params#########',request.GET.query_params)

        #Pageination
        paginator=PageNumberPagination()
        paginator.page_size=4
        result_page=paginator.paginate_queryset(products,request)

        serializer=ProductSerializers(result_page,many=True)
        # remove Unnecessary data from serializer.data to send client
        for i in serializer.data:
            i.pop('description')
        return paginator.get_paginated_response(serializer.data)


@api_view(['GET','PUT','DELETE'])
@permission_classes((IsAuthenticatedOrReadOnly,))
def product_details(request,product_slug):
    try:
        product=Product.objects.get(slug=product_slug)
    except Product.DoesNotExist:
        res = {
            'error': 'product with this Slug does not exist'
        }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

    if request.method=='GET':
        # Paginate Comments of Product + ProductDetailSerializer.get_comments
        paginator = PageNumberPagination()
        paginator.page_size = 1
        paginator.paginate_queryset(product.comments.filter(show=True), request)
        serializer = ProductDetailSerializers(product,context={'request':request})
        return paginator.get_paginated_response(serializer.data)
    elif request.method=='PUT':
        user=request.user
        if user.is_superuser:
            # Check token expire
            token_expire_handler(token=request.auth)
            # print('########req.data',request.data)
            if 'attribute' in request.data:
                attr=request.data['attribute']
                json_attr=json.loads(attr)
                names = []
                values = []
                for i in json_attr:
                    if not i.get('name') in names:
                        # print(i['name'])
                        names.append(i['name'])
                    if not i['value'] in values:
                        # print(i['value'])
                        values.append(i['value'])


                temp_attribute = Attribute.objects.filter(name__in=names, value__in=values)
                # remove old attribute
                product.attribute.clear()
                # add new attribute
                for att in temp_attribute:
                    # print('attribute:############', att)
                    product.attribute.add(att)

            # else:
            #     print('@@@@@@@@@_no1_@@@@@@@@@')

            serializer=ProductDetailSerializers(product,data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                res=serializer.data
                res['message']='update successfully'
                return Response(res,status=status.HTTP_205_RESET_CONTENT)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        res = {
            'error': 'Permission denied. You are not SuperUser'
        }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

    elif request.method=='DELETE':
        user = request.user
        if user.is_superuser:
            # Check token expire
            token_expire_handler(token=request.auth)
            product.delete()
            result = {
                'massage': 'post deleted successfully'
            }
            return Response(result, status=status.HTTP_204_NO_CONTENT)
        res={
            'error': 'Permission denied. You are not SuperUser'
        }
        return Response(res,status=status.HTTP_400_BAD_REQUEST)