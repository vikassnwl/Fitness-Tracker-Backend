from django.contrib import admin
from .models import Exercise, Workout, WorkoutExercise, ExerciseSet, Meal, MealItem, FavoriteMeal, BodyEntry

admin.site.register(Exercise)
admin.site.register(Workout)
admin.site.register(WorkoutExercise)
admin.site.register(ExerciseSet)
admin.site.register(Meal)
admin.site.register(MealItem)
admin.site.register(FavoriteMeal)
admin.site.register(BodyEntry)
