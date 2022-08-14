from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny
from .serializers import UserSerializers,ProductSerializers,CategorySerializers,\
    ProfileSerializers,AttributeSerializers,CommentSerializers,RatingSerializers,\
    ProductDetailSerializers,ChangePasswordSerializers,ProductImageSerializers,VariationsSerializers
from .models import Product,Profile,Comment,Category,Attribute,Rating,Variation,ProductImage,Basket,Coupon
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import json
from django.db.models import Avg,Max
from itertools import chain
from django.db.models import Q

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

def search_filter(products,query_param):
    discount = query_param.get('discount')
    stock = query_param.get('stock')
    max_price = query_param.get('maxprice')
    min_price = query_param.get('minprice')
    ordering = query_param.get('sort')

    if ordering:
        if ordering == 'lowprice':
            products = products.order_by('price')
        if ordering == 'highprice':
            products = products.order_by('-price')
        if ordering == 'rate':
            products = products.annotate(avg=Avg('rates__rate')).order_by('-avg')
        if ordering=='new':
            products = products.order_by('-created')
        query_param.pop('sort')

    if (max_price and min_price):
        products = products.filter(price__range=(min_price, max_price))
        print('products after price filter: ', products)
        query_param.pop('maxprice')
        query_param.pop('minprice')
    print('query_param after maxmin=', query_param)

    if discount:
        if discount == '1':
            products = products.filter(discount__isnull=False)
            print('products after discount filter: ', products)
        query_param.pop('discount')
    print('query_param after discount=', query_param)

    if stock:
        if stock == '1':
            products = products.filter(stock__gt=0)
            print('products after stock filter: ', products)
        query_param.pop('stock')
    print('query_param after stock=', query_param)
    print('query_param key=', query_param.keys())
    print('query_param value=', query_param.values())
    names = query_param.keys()
    values = []

    for item in query_param:
        for value in query_param.getlist(item):
            print('value', value)
            values.append(value)

    temp_att = Attribute.objects.filter(name__in=names, value__in=values)
    print(temp_att)

    if temp_att.exists():
        print('yes temp exist')
        # products = products.filter(attribute__)
        # this is new result
        # products2=products.filter(variations__privileged_attribute__in=temp_att).distinct()

        # products= products.filter(Q(attribute__in=temp_att) | Q(variations__privileged_attribute__in=temp_att)).distinct()
        # products= products.filter(Q(attribute__exact=temp_att) | Q(variations__privileged_attribute__exact=temp_att)).distinct()
        # products= products.filter(attribute__exact=temp_att , variations__privileged_attribute__exact=temp_att)
        for i in temp_att:
            products=products.filter(Q(attribute=i) | Q(variations__privileged_attribute=i)).distinct()
        print('products after att filter: ', products)
        # print('products2 privileged_att: ', products2)
        # products.union(products2) # not work ,just return first products
        # products=chain(products1,products2) # error
        print('products after union: ', products)

    return products

@api_view(['POST'])
@permission_classes((AllowAny,))
def search(request):
    products=Product.objects.all()
    # it = request.POST.get('search')
    # print('it search$$$$$$$$$$$$$$$$$$4$$$$$$$$$$$$$$$', it)
    item=request.data.get('search')
    print('itemin search$$$$$$$$$$$$$$$$$$4$$$$$$$$$$$$$$$',item)
    result=products.filter(Q(name__icontains=item)|Q(category__name__icontains=item)|
                           Q(attribute__value__icontains=item)|Q(category__parent__name__icontains=item)|
                           Q(variations__privileged_attribute__value__icontains=item)).distinct()
    # for postgeresql search
    # result = products.filter(Q(name__search=item) | Q(category__name__search=item) |
    #                          Q(attribute__value__search=item) | Q(category__parent__name__search=item) |
    #                          Q(variations__privileged_attribute__value__search=item)).distinct()
    # Paginator
    paginator = PageNumberPagination()
    paginator.page_size = 4
    result_page = paginator.paginate_queryset(result, request)
    serializer=ProductSerializers(result_page,many=True)
    return paginator.get_paginated_response(serializer.data)
    # return Response({'data':'yes'})

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

@api_view(['POST','PUT','DELETE'])
def add_edit_delete_product(request):
    if request.method=='POST':
        user=request.user
        if user.is_superuser:
            # Check token expire
            token_expire_handler(token=request.auth)

            temp_category=Category.objects.get(slug=request.data['category_slug'])
            # Add(get | create) selected Attribute to Product     ----------------------
            att=request.data['attribute']
            print('@@@att: ',att)

            json_att=json.loads(att)

            print('@@@json_att: ',json_att)
            temp_attribute=[]
            for i in json_att:
                print('@@@json_att.items: ',i.items())
                print('@@@json_att.keys: ',i.keys())
                print('@@@json_att.values: ',i.values())
                print('@@@i: ',i)
                name=list(i.values())[0]
                value=list(i.values())[1]
                print(f'name:{name},value:{value}')

                # att_serializer=AttributeSerializers(data=dict(i.values()),many=True)
                # if att_serializer.is_valid(raise_exception=True):
                #     att_serializer.save()

                attr,created=Attribute.objects.get_or_create(name=name,value=value)
                temp_attribute.append(attr)

            # list_att=request.data.getlist('attribute')
            # print('@@@list_json_att: ',list_att)
            # print('@@@list_json_att.items: ',list_att.items()) #error

            # names=[]
            # values=[]
            # # get the desired attributes
            # for i in json_att:
            #     if not i.get('name') in names:
            #         # print(i['name'])
            #         names.append(i['name'])
            #     if not i['value'] in values:
            #         # print(i['value'])
            #         values.append(i['value'])
            #
            # temp_attribute=Attribute.objects.filter(name__in=names,value__in=values)
            print('****temp_att***',temp_attribute)
            product=Product(category=temp_category)
            serializer = ProductSerializers(product,data=request.data)
            if serializer.is_valid():
                serializer.save()
                for i in temp_attribute:
                    # print('attribute:############', i)
                    product.attribute.add(i)

                # Add Images to Product        -------------------------------
                all_image=request.data.getlist('images')
                # all_image=request.FILES.lists()
                MAX_FILE_SIZE = 512000
                images_406=[]
                for image in all_image:
                    print('image:',image)
                    if image.size > MAX_FILE_SIZE:
                            print('$$$$$$image size: ', image.size)
                            images_406.append(image)
                            continue
                            # raise ValidationError("image size too big.The image size must be less than 500kb ")
                            # res={
                            #     'error':f'size of({image})image is too big.The image size must be less than 500kb '
                            # }
                            # return Response(res,status=status.HTTP_406_NOT_ACCEPTABLE)
                    ProductImage.objects.create(product=product,images=image)

                # Add Variations to Product        -----------------------------
                if 'var_id' in request.data:
                    var_id = request.data['var_id']
                    temp_variation=Variation.objects.filter(id__in=var_id)
                    print('var_id: ',var_id)
                    print('temp_var***** : ',temp_variation)
                    for i in var_id:
                        product.variations.add(i)
                        # product.variations.add(temp_variation)
                if 'variations' in request.data:
                    variations=request.data.get('variations')
                    json_variation=json.loads(variations)
                    print('%%%variations',variations)
                    for variation in json_variation:
                        print('%%%variation',variation)

                        att=variation['privileged_attribute']
                        print('%%%att: ', att)

                        # json_att = json.loads(att)

                        # print('%%%json_att: ', json_att)
                        temp_attribute = []
                        for i in att:
                            print('%%%json_att.items: ', i.items())
                            # print('@@@json_att.keys: ', i.keys())
                            print('%%%json_att.values: ', i.values())
                            print('%%%i: ', i)
                            name = list(i.values())[0]
                            value = list(i.values())[1]
                            print(f'name:{name},value:{value}')

                            attr, created = Attribute.objects.get_or_create(name=name, value=value)
                            temp_attribute.append(attr)

                        temp_variation=Variation(product=product)
                        variation_serializer=VariationsSerializers(temp_variation,data=variation)
                        if variation_serializer.is_valid(raise_exception=True):
                            variation_serializer.save()
                            for i in temp_attribute:
                                temp_variation.privileged_attribute.add(i)

                res=serializer.data
                if images_406:
                    res['warning']= f'images({images_406})not acceptable,because images size must be less than 500kb'
                return Response(res, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        res = {
                'error': 'Permission denied. You are not SuperUser'
            }
        return Response(res, status=status.HTTP_400_BAD_REQUEST)

    elif request.method=='PUT':
        user=request.user
        if user.is_superuser:
            # Check token expire
            token_expire_handler(token=request.auth)
            try:
                product_slug=request.data.get('product_slug')
                product=Product.objects.get(slug=product_slug)
            except Product.DoesNotExist:
                result = {
                    'error': 'product with this slug does not exist'
                }
                return Response(result, status=status.HTTP_204_NO_CONTENT)
            images_406 = []
            if 'images' in request.data:
                product.images.clear()
                all_image = request.data.getlist('images')
                MAX_FILE_SIZE = 512000
                for image in all_image:
                    if image.size > MAX_FILE_SIZE:
                        images_406.append(image)
                        continue
                    ProductImage.objects.create(product=product,images=image)

            if 'variations' in request.data:
                # product.variations.clear()
                variations = request.data.get('variations')
                json_variation = json.loads(variations)
                # remove old variation
                Variation.objects.filter(product=product).delete()
                print('%%%variations', variations)
                for variation in json_variation:
                    print('%%%variation', variation)

                    att = variation['privileged_attribute']
                    print('%%%att: ', att)

                    # json_att = json.loads(att)

                    # print('%%%json_att: ', json_att)
                    temp_attribute = []
                    for i in att:
                        print('%%%json_att.items: ', i.items())
                        # print('@@@json_att.keys: ', i.keys())
                        print('%%%json_att.values: ', i.values())
                        print('%%%i: ', i)
                        name = list(i.values())[0]
                        value = list(i.values())[1]
                        print(f'name:{name},value:{value}')

                        attr, created = Attribute.objects.get_or_create(name=name, value=value)
                        temp_attribute.append(attr)

                    temp_variation = Variation(product=product)

                    variation_serializer = VariationsSerializers(temp_variation, data=variation)
                    if variation_serializer.is_valid(raise_exception=True):
                        variation_serializer.save()
                        for i in temp_attribute:
                            temp_variation.privileged_attribute.add(i)

            if 'attribute' in request.data:
                att=request.data['attribute']
                json_att=json.loads(att)
                # names = []
                # values = []
                temp_attribute = []
                for i in json_att:
                    name = list(i.values())[0]
                    value = list(i.values())[1]
                    attr, created = Attribute.objects.get_or_create(name=name, value=value)
                    temp_attribute.append(attr)
                    # if not i.get('name') in names:
                    #     # print(i['name'])
                    #     names.append(i['name'])
                    # if not i['value'] in values:
                    #     # print(i['value'])
                    #     values.append(i['value'])

                # temp_attribute = Attribute.objects.filter(name__in=names, value__in=values)
                # remove old attribute
                product.attribute.clear()
                # add new attribute
                for att in temp_attribute:
                    # print('attribute:############', att)
                    product.attribute.add(att)

            serializer=ProductDetailSerializers(product,data=request.data,partial=True,context={'request':request})
            if serializer.is_valid():
                serializer.save()
                res=serializer.data
                res['message']='update successfully'
                if images_406:
                    res['warning']= f'images({images_406})not acceptable,because images size must be less than 500kb'
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
            try:
                product_slug=request.data.get('product_slug')
                product=Product.objects.get(slug=product_slug)
            except Product.DoesNotExist:
                result = {
                    'error': 'product with this slug does not exist'
                }
                return Response(result, status=status.HTTP_204_NO_CONTENT)

            product.delete()
            result = {
                'massage': 'product deleted successfully'
            }
            return Response(result, status=status.HTTP_204_NO_CONTENT)
        else:
            res={
                'error': 'Permission denied. You are not SuperUser'
            }
        return Response(res,status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
def products_by_category(request,category_slug):
    if request.method=='GET':
        try:
            # Product.objects.filter(att)
            products=Product.objects.filter(category__slug=category_slug)
        except Product.DoesNotExist:
            res = {
                'error': 'any product does not exist'
            }
            return Response(res, status=status.HTTP_400_BAD_REQUEST)

        # Search-Filter & Ordering     -------------------------
        query_param=request.query_params.copy()
        print('$$$query_param: ',query_param)
        if query_param :
            print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            products=search_filter(products=products,query_param=query_param)
        # query_param=request.query_params.copy()
        # discount=query_param.get('discount')
        # stock=query_param.get('stock')
        # max_price=query_param.get('maxprice')
        # min_price=query_param.get('minprice')
        # ordering=query_param.get('sort')
        #
        # if ordering:
        #     if ordering=='lowprice':
        #         products=products.order_by('price')
        #     if ordering=='highprice':
        #         products=products.order_by('-price')
        #     if ordering=='rate':
        #         products=products.annotate(avg=Avg('rates__rate')).order_by('-avg')
        #     # if ordering==''
        #     query_param.pop('sort')
        #
        # if (max_price and min_price):
        #     products=products.filter(price__range=(min_price,max_price))
        #     print('products after price filter: ',products)
        #     query_param.pop('maxprice')
        #     query_param.pop('minprice')
        # print('query_param after maxmin=',query_param)
        #
        # if discount:
        #     if discount == '1':
        #         products=products.filter(discount__isnull=False)
        #         print('products after discount filter: ', products)
        #     query_param.pop('discount')
        # print('query_param after discount=',query_param)
        #
        # if stock:
        #     if stock == '1':
        #         products=products.filter(stock__gt=0)
        #         print('products after stock filter: ', products)
        #     query_param.pop('stock')
        # print('query_param after stock=',query_param)
        # print('query_param key=',query_param.keys())
        # print('query_param value=',query_param.values())
        # names=query_param.keys()
        # values=[]
        #
        # for item in query_param:
        #     for value in query_param.getlist(item):
        #         print('value',value)
        #         values.append(value)
        #
        # temp_att=Attribute.objects.filter(name__in=names,value__in=values)
        # print(temp_att)
        #
        # if temp_att.exists():
        #     print('yes temp exist')
        #     products=products.filter(attribute__in=temp_att).distinct()
        #     print('products after att filter: ',products)
        max_price=products.aggregate(max=Max('price'))
        # att2=products.values_list('variations__privileged_attribute__name',flat=True)
        # att1=products.values_list('attribute__name',flat=True)
        # chain_attribute=list(chain(att1,att2))
        # union_attribute=list(att1.union(att2,all=True)) # error database
        # att_distinct=[]
        # for i in chain_attribute:
        #     if i not in att_distinct:
        #         att_distinct.append(i)
        print('products:',products)
        # print('products_att',(i.attribute__value for i in products))
        for i in products:
            print('i.att',i.attribute)
            print('i.att__val',i.get_attribute())
        print('end')
        attribute_value=[]
        for product in products:
            for att in product.attribute.all():
                if att not in attribute_value:
                    print('added to list:',att)
                    attribute_value.append(att)
            # for att in product.variations.values_list('privileged_attribute__value',flat=True):
            #     a=Attribute.objects.get(att)
            #     if a not in attribute_value:
            #         attribute_value.append(a)
            for var in product.variations.all():
                for att in var.privileged_attribute.all():
                    if att not in attribute_value:
                        print('add to list2',att)
                        attribute_value.append(att)
            print('****attribute****+',product,'==',attribute_value)
            # for i in product.variations.values_list('privileged_attribute',flat=True):
            # for i in product.variations.privileged_attribute.all():
            #     if i not in attribute_value:
            #         attribute_value.append(i)
                #forloop for att req
            # new=Attribute.objects.filter(products=product)
            # if new not in attribute_value:
            #     attribute_value.append(new)
            # print('****privileged_attribute****+',product,'==',attribute_value)

            #     print('!!!!####privileged_att=',att)
        print('kole value ha',attribute_value)
        # att_value2=products.values_list('variations__privileged_attribute__value',flat=True)
        # att_value1=products.values_list('attribute__value',flat=True)
        # att_value1=products.values_list('attribute',flat=True)
        #just name of att
        # for product in products:
        #     r=product.attribute.values_list('value',flat=True)
        #     print('r&&&&&=',r)
        # print('products_att_value_list',att_value1)
        # new=products.values('attribute')
        # print('products_att****',new)
        # chain_att_value=list(chain(att_value1,att_value2))
        # att_value_distinct = []
        # for i in chain_att_value:
        #     if i not in att_value_distinct:
        #         att_value_distinct.append(i)
        # final=Attribute.objects.filter(value__in=att_value_distinct)
        attribute_value = list(sorted(attribute_value, key=lambda obj:obj.name))
        attributes_serializer=AttributeSerializers(attribute_value,many=True)
        # att_val=products.values_list('attribute__value',flat=True)
        # att_val_d=products.values_list('attribute__value',flat=True).distinct() # distinct not work correctly
        # print('attribute: ',att1)
        # print('attribute2: ',att2)
        # print('chain(att2,att1): ',chain_attribute)
        # print('attribute_d: ',att_d)
        # print('attribute_distinct: ',att_distinct)

        # print('attribute_val1: ',att_value1)
        # print('attribute_val2: ',att_value2)
        # print('chain(att_val1,att_val2): ',chain_att_value)
        # print('attribute_val_d: ',att_value_distinct)
        # print('@@@final attribute: ',final)
        print('@@@final attribute_serialize: ',attributes_serializer.data)
        print('products:',products)
        filters = {
            'ordering': {
                'type': 'Inline Radio',
                'options': ['new', 'rate', 'lowprice', 'highprice']
            },
            'price': {
                'type': 'Range Slider',
                'options': {'minprice': 0, 'maxprice': max_price['max']}

            },
            'discount': {
                'type': 'Toggle Switch'
            },
            'stock': {
                'type': 'Toggle Switch'
            },
            'attribute':{
                'type': 'Select Box',
                'options': {'attributes':attributes_serializer.data}
            }
        }

        #Pageination
        paginator=PageNumberPagination()
        paginator.page_size=4
        result_page=paginator.paginate_queryset(products,request)

        serializer=ProductSerializers(result_page,many=True)
        # remove Unnecessary data from serializer.data to send client
        for i in serializer.data:
            i.pop('description')
        # max_price=products.annotate(max=Max('price'))
        # print('****$$$$max-price with annotate:',max_price)
        # print('****$$$$max-price with annotate[]:',max_price['max'])
        print('****$$$$max-price with aggrigate[]:',max_price['max'])
        data={}
        data['products']=serializer.data
        data['filters']=filters
        # serializer.data.update({'filters':filters})#error : has no attribute update
        # return paginator.get_paginated_response(serializer.data)
        return paginator.get_paginated_response(data)
        # response=paginator.get_paginated_response(serializer.data)
        # response['filters']=filters
        # return response


@api_view(['GET'])
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

