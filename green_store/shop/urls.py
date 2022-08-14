from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    # Authentication section
    path('register/',views.register,name='register'),
    path('login/',obtain_auth_token,name='login'),
    path('logout/',views.logout,name='logout'),
    path('change_password/',views.change_password,name='change_password'),
    path('profile/',views.profile,name='profile'),
    # Other
    path('get_started/',views.get_started,name='home'), # in view return thing same as best_rating,new,off,...
    path('category/',views.category,name='category'),
    path('attribute/',views.attribute,name='attribute'),
    path('comment/',views.comment,name='comment'),
    path('rating/',views.rating,name='rating'),
    # Search
    path('search/',views.search,name='search'),
    # Product section
    path('add_edit_delete_product/',views.add_edit_delete_product,name='add_edit_delete_product'),
    path('products/<slug:product_slug>', views.product_details, name='product_detail'),
    path('<slug:category_slug>',views.products_by_category,name='products_by_category'),

 ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)