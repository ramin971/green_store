# Generated by Django 4.0.5 on 2022-09-11 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_remove_orderitem_attribute_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basket',
            name='provide_order',
        ),
        migrations.RemoveField(
            model_name='basket',
            name='send_order',
        ),
        migrations.AddField(
            model_name='basket',
            name='status',
            field=models.CharField(choices=[('queue', 'Queue'), ('providing', 'Providing'), ('sent', 'Sent')], default='queue', max_length=10),
        ),
    ]
