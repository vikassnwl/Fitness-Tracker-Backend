import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

# Existing library rows stay with vikassnwl; also ensure split-template names are saved for them.
VIKASSNWL_EXERCISES = [
    'Bench Press',
    'Inclined Chest Press',
    'Barbell Shoulder Press',
    'Chest Pec Dec Fly',
    'Shoulder Side Raises',
    'Tricep Rope Push Down',
    'Tricep Overhead Extension',
    'Wide grip lat pull down',
    'seated cable rows',
    'single arm dumbbell rows',
    'T bar rows',
    'Rear delts',
    'barbell curls',
    'hammer curls',
    'barbell squats',
    'leg press',
    'walking db lunges',
    'leg curl',
    'leg extension',
    'calf raises',
]


def assign_and_seed_exercises_for_vikassnwl(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Exercise = apps.get_model('api', 'Exercise')

    owner, _ = User.objects.get_or_create(
        username='vikassnwl',
        defaults={'email': ''},
    )
    Exercise.objects.filter(user__isnull=True).update(user=owner)

    existing_names = {
        name.lower()
        for name in Exercise.objects.filter(user=owner).values_list('name', flat=True)
    }
    for name in VIKASSNWL_EXERCISES:
        if name.lower() not in existing_names:
            Exercise.objects.create(user=owner, name=name)
            existing_names.add(name.lower())


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0005_add_meal5_to_dietlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='user',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='exercises',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(assign_and_seed_exercises_for_vikassnwl, noop_reverse),
        migrations.AlterField(
            model_name='exercise',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='exercises',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterModelOptions(
            name='exercise',
            options={'ordering': ['name']},
        ),
        migrations.AlterUniqueTogether(
            name='exercise',
            unique_together={('user', 'name')},
        ),
    ]
