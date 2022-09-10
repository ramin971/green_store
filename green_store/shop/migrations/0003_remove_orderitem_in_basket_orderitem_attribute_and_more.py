# Generated by Django 4.0.5 on 2022-09-05 14:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_alter_basket_ordered_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='in_basket',
        ),
        migrations.AddField(
            model_name='orderitem',
            name='attribute',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='shop.attribute'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='privileged_attribute',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='order_item', to='shop.attribute'),
        ),
    ]