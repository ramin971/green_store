from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('register/',views.register,name='register'),
    path('login/',obtain_auth_token,name='login'),
    path('get_started/',views.get_started,name='home'), # in view return thing same as best_rating,new,off,...
    path('category/',views.category,name='category'),
    # path('products/<slug:pn>',details,name='product_detail'),
    # path('<slug:p_category>/<slug:category>/',all_products, name = 'all_products'),
    # path('',,name=''),
    # path('',,name=''),
    # path('',,name=''),
 ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)