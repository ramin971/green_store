from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MaxValueValidator,MinValueValidator,RegexValidator
# Create your models here.


class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    f_name=models.CharField(max_length=50)
    l_name=models.CharField(max_length=50)
    address=models.CharField(max_length=300)
    email=models.EmailField()
    postal_code=models.CharField(validators=[RegexValidator(regex='^\d{10}$',message='must be 10 digit',code='invalid_postal_code')],max_length=10)
    phone=models.CharField(validators=[RegexValidator(regex='^[0][9][0-3][0-9]{8}$',message='phone number invalid',code='invalid_phone')],max_length=11,unique=True)
    created=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.user.username

class Attribute(models.Model):
    name=models.CharField(max_length=50)
    value=models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name','value'],name='unique_attribute')
        ]

    def __str__(self):
        return '{} ->\n{}\n'.format(self.name,self.value)


class Category(models.Model):
    name=models.CharField(max_length=50,unique=True)
    slug=models.SlugField(unique=True)
    parent=models.ForeignKey('self',on_delete=models.CASCADE,blank=True,null=True,related_name='child')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['slug', 'parent'], name="unique_slug_category"),
        ]

    def save(self,*args,**kwargs):
        self.slug=slugify(self.name)
        super(Category,self).save(*args,**kwargs)


    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent

        return ' -> '.join(full_path[::-1])



class Product(models.Model):
    name=models.CharField(max_length=100,unique=True)
    # image=models.ImageField(upload_to='images',max_length=512000)
    attribute=models.ManyToManyField(Attribute,blank=True,related_name='products')
    price=models.PositiveIntegerField()
    discount=models.PositiveSmallIntegerField(null=True,blank=True,validators=[MinValueValidator(1),MaxValueValidator(99)])
    slug=models.SlugField(unique=True,db_index=True)
    category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,related_name='products')
    description=models.TextField(blank=True,null=True)
    stock=models.PositiveSmallIntegerField()
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=('-created',)

    def save(self,*args,**kwargs):
        self.slug=slugify(self.name)
        super(Product,self).save(*args,**kwargs)

    def get_attribute(self):
        return ',\n'.join([str(p) for p in self.attribute.all()])

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    images=models.ImageField(upload_to='images/%Y/%m/%d/',max_length=512000)
    product=models.ForeignKey(Product,on_delete=models.CASCADE,null=True,related_name='images')
    def __str__(self):
        return str(self.product)

class Variation(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='variations')
    privileged_attribute=models.ManyToManyField(Attribute,related_name='privileged_att')
    price=models.PositiveIntegerField()
    stock=models.PositiveSmallIntegerField()
    created=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.product)

    def get_privileged_att(self):
        return ',\n'.join([str(p) for p in self.privileged_attribute.all()])
# class OrderItem(models.Model):
#     product=models.ForeignKey(Product,on_delete=models.CASCADE)
#     quantity=models.PositiveSmallIntegerField(default=1)


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.code


# class Oreder(models.Model):
#     user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='order')
#     coupon=models.ForeignKey(Coupon,on_delete=models.SET_NULL,null=True,blank=True)

class Basket(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='basket')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)
    coupon=models.ForeignKey(Coupon,on_delete=models.SET_NULL,null=True,blank=True)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=['user','coupon'],name='uniq_coupon')
        ]

class Comment(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='comments')
    text=models.TextField()
    show=models.BooleanField(default=False)
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='comments')
    # def __str__(self):
    #     return self.pk

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rates')
    rate = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(5)])
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='rates')

    # class Meta:
    #     constraints=[
    #         models.UniqueConstraint(fields=['user','product'],name='uniq_rating')
    #     ]

