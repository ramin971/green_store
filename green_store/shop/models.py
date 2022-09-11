from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MaxValueValidator,MinValueValidator,RegexValidator
from rest_framework.exceptions import NotAcceptable
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
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='images')
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
    STATUS_CHOICES=(('queue','Queue'),('providing','Providing'),('sent','Sent'))
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='baskets')
    tracking_code=models.CharField(max_length=8,blank=True,null=True,unique=True)
    # order_items = models.ManyToManyField(OrderItem)
    ordered_date = models.DateTimeField(null=True,blank=True)
    coupon = models.ForeignKey(Coupon,on_delete=models.SET_NULL,null=True,blank=True)
    payment = models.BooleanField(default=False)
    status=models.CharField(max_length=10,choices=STATUS_CHOICES,default='queue')
    # send_order = models.BooleanField(default=False)

    class Meta:
        constraints=[
            # models.UniqueConstraint(fields=['payment','user'], condition=Q(payment=False), name='unique_free_basket'), # not work
            models.UniqueConstraint(fields=['user','coupon'],name='uniq_coupon'),

        ]


    def __str__(self):
        return f'{self.user.username} , {self.id}'


    def get_total_price(self):
        total=0
        for order_item in self.order_items.all():
            total += order_item.get_total_product_price()

        if self.coupon:
            total -= self.coupon.amount

        return total


    def get_order_items(self):
        return ',\n'.join([str(p) for p in self.order_items.all()])

    # Limit each User to have one Basket(payment=False)
    def save(self,*args,**kwargs):
        if not self.payment:
            try:
                temp=Basket.objects.get(user=self.user ,payment=False)
                print('temp*******',temp)
                # print('temp-value*******',temp._meta.get_fields())
                if self != temp:
                    raise NotAcceptable('basket is exist')
                super(Basket,self).save(*args,**kwargs)

            except Basket.DoesNotExist:
                print('basket not exist***')
                # super(Basket,self).save(*args,**kwargs)
        super(Basket, self).save(*args, **kwargs)




class OrderItem(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='order_items')
    basket = models.ForeignKey(Basket,on_delete=models.CASCADE,related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)
    variation = models.ForeignKey(Variation,on_delete=models.CASCADE,null=True,blank=True,related_name='order_items')
    # attribute = models.OneToOneField(Attribute,on_delete=models.CASCADE,null=True,blank=True,related_name='order_item')
    # in_basket = models.BooleanField(default=True)
    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(fields=['attribute','attribute__name'],name='unique_basket_var')
    #         models.UniqueConstraint(fields=['attribute__name'],name='unique_basket_var')
    #         # models.UniqueConstraint(fields=['attribute'], condition=Q(attribute.name=unique), name='unique_free_basket'), # not work
    #
    #     ]

    def __str__(self):
        if self.variation:
            return f'>{self.product.name}-{list(self.variation.privileged_attribute.values_list("value",flat=True))}({self.quantity})#'
        else:
            return f'>{self.product.name}({self.quantity})#'

        # return f'{self.quantity} of {self.product.name}'

    def get_total_product_price(self):
        if self.variation:
            return self.quantity * self.variation.price
        elif self.product.discount:
            old_price=self.product.price
            discount=self.product.discount
            new_price = old_price - (discount * old_price // 100)
            return self.quantity * new_price
        else:
            return self.quantity * self.product.price



class Comment(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='comments')
    text=models.TextField()
    show=models.BooleanField(default=False)
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='comments')
    # def __str__(self):
    #     return self.pk
    class Meta:
        ordering=('-id',)
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rates')
    rate = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(5)])
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='rates')

    # class Meta:
    #     constraints=[
    #         models.UniqueConstraint(fields=['user','product'],name='uniq_rating')
    #     ]

