import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_existing_rows_to_owner(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    owner = User.objects.filter(username='vikassnwl').first()
    if owner is None:
        owner = User.objects.order_by('id').first()
    if owner is None:
        return

    for model_name in ('Workout', 'Meal', 'FavoriteMeal', 'BodyEntry', 'DietLog'):
        Model = apps.get_model('api', model_name)
        Model.objects.filter(user__isnull=True).update(user=owner)


def noop_reverse(apps, schema_editor):
    pass


def add_nullable_user(model_name, related_name):
    return migrations.AddField(
        model_name=model_name,
        name='user',
        field=models.ForeignKey(
            null=True,
            on_delete=django.db.models.deletion.CASCADE,
            related_name=related_name,
            to=settings.AUTH_USER_MODEL,
        ),
    )


def alter_required_user(model_name, related_name):
    return migrations.AlterField(
        model_name=model_name,
        name='user',
        field=models.ForeignKey(
            on_delete=django.db.models.deletion.CASCADE,
            related_name=related_name,
            to=settings.AUTH_USER_MODEL,
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0007_splitdayexercise'),
    ]

    operations = [
        add_nullable_user('workout', 'workouts'),
        add_nullable_user('meal', 'meals'),
        add_nullable_user('favoritemeal', 'favorite_meals'),
        add_nullable_user('bodyentry', 'body_entries'),
        add_nullable_user('dietlog', 'diet_logs'),
        migrations.RunPython(assign_existing_rows_to_owner, noop_reverse),
        alter_required_user('workout', 'workouts'),
        alter_required_user('meal', 'meals'),
        alter_required_user('favoritemeal', 'favorite_meals'),
        alter_required_user('bodyentry', 'body_entries'),
        alter_required_user('dietlog', 'diet_logs'),
        migrations.AlterField(
            model_name='dietlog',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterUniqueTogether(
            name='dietlog',
            unique_together={('user', 'date')},
        ),
    ]
