# Generated by Django 3.0.5 on 2020-05-19 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0008_auto_20200519_1517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(upload_to='backend/bug_images/<property object at 0x7f7e01b014a8>'),
        ),
        migrations.AlterField(
            model_name='user',
            name='enrollment_no',
            field=models.CharField(max_length=15, unique=True),
        ),
    ]
