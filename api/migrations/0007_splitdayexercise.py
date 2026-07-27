from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

SEED_SPLIT_EXERCISES = {
    'push': [
        'Bench Press',
        'Inclined Chest Press',
        'Barbell Shoulder Press',
        'Chest Pec Dec Fly',
        'Shoulder Side Raises',
        'Tricep Rope Push Down',
        'Tricep Overhead Extension',
    ],
    'pull': [
        'Wide grip lat pull down',
        'seated cable rows',
        'single arm dumbbell rows',
        'T bar rows',
        'Rear delts',
        'barbell curls',
        'hammer curls',
    ],
    'legs': [
        'barbell squats',
        'leg press',
        'walking db lunges',
        'leg curl',
        'leg extension',
        'calf raises',
    ],
}


def seed_vikassnwl_split_templates(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Exercise = apps.get_model('api', 'Exercise')
    SplitDayExercise = apps.get_model('api', 'SplitDayExercise')

    try:
        owner = User.objects.get(username='vikassnwl')
    except User.DoesNotExist:
        return

    exercises_by_name = {
        (exercise.name or '').strip().lower(): exercise
        for exercise in Exercise.objects.filter(user=owner)
    }

    for split, names in SEED_SPLIT_EXERCISES.items():
        for order, name in enumerate(names):
            key = name.strip().lower()
            exercise = exercises_by_name.get(key)
            if not exercise:
                exercise = Exercise.objects.create(user=owner, name=name)
                exercises_by_name[key] = exercise

            SplitDayExercise.objects.get_or_create(
                user=owner,
                split=split,
                exercise=exercise,
                defaults={'order': order},
            )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0006_exercise_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='SplitDayExercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('split', models.CharField(choices=[('push', 'Push'), ('pull', 'Pull'), ('legs', 'Legs')], max_length=20)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='split_assignments', to='api.exercise')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='split_day_exercises', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['split', 'order', 'id'],
                'unique_together': {('user', 'split', 'exercise')},
            },
        ),
        migrations.RunPython(seed_vikassnwl_split_templates, noop_reverse),
    ]
