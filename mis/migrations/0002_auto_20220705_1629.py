# Generated by Django 3.2.4 on 2022-07-05 16:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mis', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ahsession',
            old_name='adolescent',
            new_name='adolescent_name',
        ),
        migrations.RenameField(
            model_name='dlsession',
            old_name='adolescent',
            new_name='adolescent_name',
        ),
    ]