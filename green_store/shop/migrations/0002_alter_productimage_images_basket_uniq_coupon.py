# Generated by Django 4.0.5 on 2022-07-26 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productimage',
            name='images',
            field=models.ImageField(max_length=512000, upload_to='images/%Y/%m/%d/'),
        ),
        migrations.AddConstraint(
            model_name='basket',
            constraint=models.UniqueConstraint(fields=('user', 'coupon'), name='uniq_coupon'),
        ),
    ]