from django.db import models

MEAL_TYPES = [
    ('breakfast', 'Breakfast'),
    ('lunch', 'Lunch'),
    ('dinner', 'Dinner'),
    ('snacks', 'Snacks'),
]
SPLIT_CHOICES = [
    ('push', 'Push'),
    ('pull', 'Pull'),
    ('legs', 'Legs'),
    ('upper', 'Upper'),
    ('lower', 'Lower'),
    ('full', 'Full Body'),
    ('custom', 'Custom'),
]

class Exercise(models.Model):
    name = models.CharField(max_length=120)
    muscle_group = models.CharField(max_length=80, blank=True)
    equipment = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Workout(models.Model):
    name = models.CharField(max_length=120, default='Untitled Workout')
    workout_type = models.CharField(max_length=20, choices=SPLIT_CHOICES, default='full')
    date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-date']

    def __str__(self):
        return f'{self.name} ({self.workout_type.title()})'

class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, related_name='exercises', on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, related_name='workout_entries', on_delete=models.CASCADE, null=True, blank=True)
    custom_name = models.CharField(max_length=120, blank=True)
    target_reps = models.PositiveIntegerField(default=0)
    target_sets = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['workout', 'order']

    def name(self):
        return self.custom_name or (self.exercise.name if self.exercise else 'Exercise')

    def __str__(self):
        return self.name()

class ExerciseSet(models.Model):
    workout_exercise = models.ForeignKey(WorkoutExercise, related_name='sets', on_delete=models.CASCADE)
    set_number = models.PositiveIntegerField(default=1)
    weight = models.FloatField(default=0)
    reps = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['set_number']

class Meal(models.Model):
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, default='breakfast')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

class MealItem(models.Model):
    meal = models.ForeignKey(Meal, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    quantity = models.CharField(max_length=80, blank=True)
    calories = models.PositiveIntegerField(default=0)
    protein = models.FloatField(default=0)
    carbs = models.FloatField(default=0)
    fat = models.FloatField(default=0)

class FavoriteMeal(models.Model):
    name = models.CharField(max_length=120)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, default='breakfast')
    notes = models.TextField(blank=True)
    items = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class BodyEntry(models.Model):
    date = models.DateField()
    weight = models.FloatField(null=True, blank=True)
    body_fat = models.FloatField(null=True, blank=True)
    chest = models.FloatField(null=True, blank=True)
    waist = models.FloatField(null=True, blank=True)
    arms = models.FloatField(null=True, blank=True)
    legs = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'{self.date} body entry'

class DietLog(models.Model):
    date = models.DateField(unique=True)
    meal1 = models.BooleanField(default=False)
    meal2 = models.BooleanField(default=False)
    meal3 = models.BooleanField(default=False)
    meal4 = models.BooleanField(default=False)
    meal5 = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'Diet log for {self.date}'
