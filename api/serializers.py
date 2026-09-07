from rest_framework import serializers
from .models import (
    Exercise, SplitDayExercise, Workout, WorkoutExercise, ExerciseSet,
    Meal, MealItem, FavoriteMeal, BodyEntry, DietLog, DayNote,
)

class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'name', 'muscle_group', 'equipment', 'notes', 'created_at']
        read_only_fields = ['created_at']


class SplitDayExerciseSerializer(serializers.ModelSerializer):
    exercise_detail = ExerciseSerializer(source='exercise', read_only=True)
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    muscle_group = serializers.CharField(source='exercise.muscle_group', read_only=True)
    equipment = serializers.CharField(source='exercise.equipment', read_only=True)

    class Meta:
        model = SplitDayExercise
        fields = [
            'id', 'split', 'exercise', 'order', 'created_at',
            'exercise_detail', 'exercise_name', 'muscle_group', 'equipment',
        ]
        read_only_fields = ['created_at', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            self.fields['exercise'].queryset = Exercise.objects.filter(user=request.user)

class ExerciseSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            self.fields['workout_exercise'].queryset = WorkoutExercise.objects.filter(
                workout__user=request.user
            )


class WorkoutExerciseSerializer(serializers.ModelSerializer):
    sets = ExerciseSetSerializer(many=True, read_only=True)
    exercise_name = serializers.SerializerMethodField()
    muscle_group = serializers.SerializerMethodField()
    equipment = serializers.SerializerMethodField()

    class Meta:
        model = WorkoutExercise
        fields = ['id', 'workout', 'exercise', 'custom_name', 'exercise_name', 'muscle_group', 'equipment', 'target_reps', 'target_sets', 'notes', 'order', 'sets']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            self.fields['workout'].queryset = Workout.objects.filter(user=request.user)
            self.fields['exercise'].queryset = Exercise.objects.filter(user=request.user)

    def get_exercise_name(self, obj):
        return obj.custom_name or (obj.exercise.name if obj.exercise else None)

    def get_muscle_group(self, obj):
        return obj.exercise.muscle_group if obj.exercise else ''

    def get_equipment(self, obj):
        return obj.exercise.equipment if obj.exercise else ''


class NestedExerciseSetWriteSerializer(serializers.Serializer):
    set_number = serializers.IntegerField(min_value=1, required=False, default=1)
    weight = serializers.FloatField(required=False, default=0)
    reps = serializers.IntegerField(min_value=0, required=False, default=0)
    completed = serializers.BooleanField(required=False, default=False)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class NestedWorkoutExerciseWriteSerializer(serializers.Serializer):
    exercise = serializers.IntegerField(required=False, allow_null=True)
    custom_name = serializers.CharField(required=False, allow_blank=True, default='')
    target_reps = serializers.IntegerField(required=False, default=0)
    target_sets = serializers.IntegerField(required=False, default=0)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    order = serializers.IntegerField(required=False, default=0)
    sets = NestedExerciseSetWriteSerializer(many=True, required=False, default=list)


class WorkoutSetUpdateItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    weight = serializers.FloatField(required=False, default=0)
    reps = serializers.IntegerField(min_value=0, required=False, default=0)
    completed = serializers.BooleanField(required=False, default=False)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class WorkoutSerializer(serializers.ModelSerializer):
    exercises = WorkoutExerciseSerializer(many=True, read_only=True)
    exercise_logs = NestedWorkoutExerciseWriteSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Workout
        fields = [
            'id', 'name', 'workout_type', 'date', 'notes', 'created_at',
            'exercises', 'exercise_logs',
        ]
        read_only_fields = ['created_at']

    def create(self, validated_data):
        exercise_logs = validated_data.pop('exercise_logs', [])
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        workout = Workout.objects.create(**validated_data)

        for index, exercise_data in enumerate(exercise_logs):
            sets_data = exercise_data.pop('sets', [])
            exercise_id = exercise_data.pop('exercise', None)
            exercise = None
            if exercise_id is not None:
                exercise = Exercise.objects.filter(id=exercise_id, user=user).first()
                if exercise is None:
                    raise serializers.ValidationError({'exercise_logs': f'Exercise {exercise_id} not found.'})

            workout_exercise = WorkoutExercise.objects.create(
                workout=workout,
                exercise=exercise,
                custom_name=exercise_data.get('custom_name', ''),
                target_reps=exercise_data.get('target_reps', 0),
                target_sets=exercise_data.get('target_sets', 0),
                notes=exercise_data.get('notes', ''),
                order=exercise_data.get('order', index),
            )
            ExerciseSet.objects.bulk_create([
                ExerciseSet(
                    workout_exercise=workout_exercise,
                    set_number=set_data.get('set_number', i + 1),
                    weight=set_data.get('weight', 0) or 0,
                    reps=set_data.get('reps', 0) or 0,
                    completed=bool(set_data.get('completed', False)),
                    notes=set_data.get('notes', '') or '',
                )
                for i, set_data in enumerate(sets_data)
            ])

        return workout

class MealItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealItem
        fields = '__all__'

class MealSerializer(serializers.ModelSerializer):
    items = MealItemSerializer(many=True)

    class Meta:
        model = Meal
        fields = ['id', 'date', 'meal_type', 'notes', 'created_at', 'items']
        read_only_fields = ['created_at']

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
        fields = ['id', 'name', 'meal_type', 'notes', 'items', 'created_at']
        read_only_fields = ['created_at']


class BodyEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyEntry
        fields = [
            'id', 'date', 'weight', 'body_fat', 'chest', 'waist',
            'arms', 'legs', 'notes', 'created_at',
        ]
        read_only_fields = ['created_at']


class DietLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietLog
        fields = ['id', 'date', 'meal1', 'meal2', 'meal3', 'meal4', 'meal5', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class DayNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DayNote
        fields = ['id', 'date', 'reason', 'note', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
