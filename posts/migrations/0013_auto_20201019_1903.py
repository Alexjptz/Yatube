# Generated by Django 2.2.6 on 2020-10-19 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0012_auto_20201019_1857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='posts/', verbose_name='Изображение'),
        ),
    ]
