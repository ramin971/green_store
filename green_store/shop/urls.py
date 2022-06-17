from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('register/',views.register,name='register'),
    path('login/',obtain_auth_token,name='login'),
    path('profile/',views.profile,name='profile'),
    path('get_started/',views.get_started,name='home'), # in view return thing same as best_rating,new,off,...
    path('category/',views.category,name='category'),
    path('attribute/',views.attribute,name='attribute'),
    path('comment/',views.comment,name='comment'),
    path('rating/',views.rating,name='rating'),
    path('addproduct/',views.add_product,name='add_product'),
    path('products/<slug:product_slug>', views.product_details, name='product_detail'),
    path('<slug:category_slug>',views.product_by_category,name='products_by_category'),

 ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)