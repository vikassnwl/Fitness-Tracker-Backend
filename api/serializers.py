from rest_framework import serializers
from .models import Exercise, Workout, WorkoutExercise, ExerciseSet, Meal, MealItem, FavoriteMeal, BodyEntry, DietLog

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = '__all__'

class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = '__all__'

class WorkoutExerciseSerializer(serializers.ModelSerializer):
    sets = ExerciseSetSerializer(many=True, read_only=True)
    exercise_name = serializers.SerializerMethodField()
    muscle_group = serializers.SerializerMethodField()
    equipment = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutExercise
        fields = ['id', 'workout', 'exercise', 'custom_name', 'exercise_name', 'muscle_group', 'equipment', 'target_reps', 'target_sets', 'notes', 'order', 'sets']

    def get_exercise_name(self, obj):
        return obj.custom_name or (obj.exercise.name if obj.exercise else None)

    def get_muscle_group(self, obj):
        return obj.exercise.muscle_group if obj.exercise else ''

    def get_equipment(self, obj):
        return obj.exercise.equipment if obj.exercise else ''

class WorkoutSerializer(serializers.ModelSerializer):
    exercises = WorkoutExerciseSerializer(many=True, read_only=True)

    class Meta:
        model = Workout
        fields = ['id', 'name', 'workout_type', 'date', 'notes', 'created_at', 'exercises']

class MealItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealItem
        fields = '__all__'

class MealSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True)

    class Meta:
        model = Meal
        fields = ['id', 'date', 'meal_type', 'notes', 'created_at', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        meal = Meal.objects.create(**validated_data)
        for item_data in items_data:
            MealItem.objects.create(meal=meal, **item_data)
        return meal

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                MealItem.objects.create(meal=instance, **item_data)
        return instance

class FavoriteMealSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteMeal
        fields = '__all__'

class BodyEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyEntry
        fields = '__all__'

class DietLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietLog
        fields = ['id', 'date', 'meal1', 'meal2', 'meal3', 'meal4', 'meal5', 'created_at', 'updated_at']
