# Generated by Django 3.0.5 on 2020-06-03 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0007_auto_20200603_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(upload_to='backend/bug_images/<django.db.models.fields.related.ForeignKey>'),
        ),
    ]
