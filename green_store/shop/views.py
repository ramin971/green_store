from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly
from .serializers import UserSerializers,ProductSerializers,CategorySerializers,ProfileSerializers
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
@permission_classes((IsAuthenticated,))
def profile(request):
    try:
        user=request.user
        print(user)
    except User.DoesNotExist:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

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


@api_view(['GET','POST'])
def category(request):
    if request.method=='GET':
        all_category=Category.objects.all()
        serializer=CategorySerializers(all_category,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    if request.method=='POST':
        serializer=CategorySerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

