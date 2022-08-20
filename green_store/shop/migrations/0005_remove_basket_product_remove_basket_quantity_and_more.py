# Generated by Django 4.0.5 on 2022-08-19 09:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shop', '0004_attribute_unique_attribute'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basket',
            name='product',
        ),
        migrations.RemoveField(
            model_name='basket',
            name='quantity',
        ),
        migrations.AddField(
            model_name='basket',
            name='ordered_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='basket',
            name='payment',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='basket',
            name='provide_order',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='basket',
            name='send_order',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='basket',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='baskets', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveSmallIntegerField(default=1)),
                ('in_basket', models.BooleanField(default=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='basket',
            name='order_items',
            field=models.ManyToManyField(to='shop.orderitem'),
        ),
    ]
