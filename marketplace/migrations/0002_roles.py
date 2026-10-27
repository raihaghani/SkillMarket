from django.db import migrations

def create_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    roles = {'Buyer': {'listing':['view'], 'offer':['add','view'], 'review':['add','view']},
             'Seller': {'listing':['add','view','change','delete'], 'offer':['view','change'], 'review':['view']}}
    for role, models in roles.items():
        group, _ = Group.objects.get_or_create(name=role)
        for model, actions in models.items():
            ct, _ = ContentType.objects.get_or_create(app_label='marketplace', model=model)
            for action in actions:
                permission, _ = Permission.objects.get_or_create(content_type=ct, codename=f'{action}_{model}', defaults={'name':f'Can {action} {model}'})
                group.permissions.add(permission)

class Migration(migrations.Migration):
    dependencies = [('marketplace','0001_initial'), ('auth','0012_alter_user_first_name_max_length')]
    operations = [migrations.RunPython(create_roles, migrations.RunPython.noop)]
