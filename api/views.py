from datetime import date, timedelta
from django.db.models import Count, FloatField, Max, Sum, F, Q
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Exercise, SplitDayExercise, Workout, WorkoutExercise, ExerciseSet,
    Meal, FavoriteMeal, BodyEntry, DietLog, DayNote,
)
from .serializers import (
    ExerciseSerializer, SplitDayExerciseSerializer, WorkoutSerializer, WorkoutExerciseSerializer,
    ExerciseSetSerializer, MealSerializer, FavoriteMealSerializer, BodyEntrySerializer, DietLogSerializer,
    WorkoutSetUpdateItemSerializer, DayNoteSerializer,
)

VALID_SPLITS = {'push', 'pull', 'legs'}


class ExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSerializer

    def get_queryset(self):
        return Exercise.objects.filter(user=self.request.user).order_by('name')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])
        exercises = self.get_queryset().filter(
            Q(name__icontains=query) | Q(muscle_group__icontains=query)
        )[:20]
        serializer = self.get_serializer(exercises, many=True)
        return Response(serializer.data)


class SplitDayExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = SplitDayExerciseSerializer
    pagination_class = None

    def get_queryset(self):
        qs = SplitDayExercise.objects.filter(user=self.request.user).select_related('exercise')
        split = self.request.query_params.get('split')
        if split in VALID_SPLITS:
            qs = qs.filter(split=split)
        return qs.order_by('order', 'id')

    def perform_create(self, serializer):
        split = serializer.validated_data['split']
        if split not in VALID_SPLITS:
            raise serializers.ValidationError({'split': 'Invalid split.'})
        next_order = SplitDayExercise.objects.filter(user=self.request.user, split=split).count()
        serializer.save(user=self.request.user, order=next_order)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Accepts: [{"id": 1, "order": 0}, {"id": 2, "order": 1}, ...]
        """
        items = request.data
        if not isinstance(items, list):
            return Response({'error': 'Expected a list'}, status=status.HTTP_400_BAD_REQUEST)
        owned_ids = set(
            SplitDayExercise.objects.filter(user=request.user).values_list('id', flat=True)
        )
        for item in items:
            entry_id = item.get('id')
            if entry_id not in owned_ids:
                continue
            SplitDayExercise.objects.filter(id=entry_id, user=request.user).update(order=item['order'])
        return Response({'status': 'ok'})


class WorkoutViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutSerializer
    pagination_class = None

    def get_queryset(self):
        qs = Workout.objects.filter(user=self.request.user).prefetch_related(
            'exercises__sets', 'exercises__exercise'
        )
        params = self.request.query_params
        date_exact = params.get('date')
        date_after = params.get('date_after')
        date_before = params.get('date_before')
        workout_type = params.get('workout_type')

        if date_exact:
            qs = qs.filter(date=date_exact)
        if date_after:
            qs = qs.filter(date__gte=date_after)
        if date_before:
            qs = qs.filter(date__lte=date_before)
        if workout_type:
            qs = qs.filter(workout_type__iexact=workout_type)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        workout = self.get_queryset().get(pk=serializer.instance.pk)
        output = WorkoutSerializer(workout, context={'request': request})
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['put'])
    def save_log(self, request, pk=None):
        """
        Bulk-update set values for an owned workout in one request.
        Body: { "sets": [{ "id", "weight", "reps", "completed", "notes" }, ...] }
        """
        workout = self.get_object()
        serializer = WorkoutSetUpdateItemSerializer(data=request.data.get('sets', []), many=True)
        serializer.is_valid(raise_exception=True)

        owned_sets = {
            item.id: item
            for item in ExerciseSet.objects.filter(workout_exercise__workout=workout)
        }
        to_update = []
        for item in serializer.validated_data:
            exercise_set = owned_sets.get(item['id'])
            if exercise_set is None:
                continue
            exercise_set.weight = item.get('weight', 0) or 0
            exercise_set.reps = item.get('reps', 0) or 0
            exercise_set.completed = bool(item.get('completed', False))
            exercise_set.notes = item.get('notes', '') or ''
            to_update.append(exercise_set)

        if to_update:
            ExerciseSet.objects.bulk_update(to_update, ['weight', 'reps', 'completed', 'notes'])

        workout = self.get_queryset().get(pk=workout.pk)
        return Response(WorkoutSerializer(workout, context={'request': request}).data)


class WorkoutExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutExerciseSerializer

    def get_queryset(self):
        return WorkoutExercise.objects.filter(
            workout__user=self.request.user
        ).prefetch_related('sets')

    def perform_create(self, serializer):
        workout = serializer.validated_data['workout']
        if workout.user_id != self.request.user.id:
            raise serializers.ValidationError({'workout': 'Not found.'})
        exercise = serializer.validated_data.get('exercise')
        if exercise is not None and exercise.user_id != self.request.user.id:
            raise serializers.ValidationError({'exercise': 'Not found.'})
        serializer.save()

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Accepts: [{"id": 1, "order": 0}, {"id": 2, "order": 1}, ...]
        Updates order for each WorkoutExercise.
        """
        items = request.data
        if not isinstance(items, list):
            return Response({'error': 'Expected a list'}, status=status.HTTP_400_BAD_REQUEST)
        owned_ids = set(
            WorkoutExercise.objects.filter(workout__user=request.user).values_list('id', flat=True)
        )
        for item in items:
            entry_id = item.get('id')
            if entry_id not in owned_ids:
                continue
            WorkoutExercise.objects.filter(
                id=entry_id, workout__user=request.user
            ).update(order=item['order'])
        return Response({'status': 'ok'})


class ExerciseSetViewSet(viewsets.ModelViewSet):
    serializer_class = ExerciseSetSerializer

    def get_queryset(self):
        return ExerciseSet.objects.filter(workout_exercise__workout__user=self.request.user)

    def perform_create(self, serializer):
        workout_exercise = serializer.validated_data['workout_exercise']
        if workout_exercise.workout.user_id != self.request.user.id:
            raise serializers.ValidationError({'workout_exercise': 'Not found.'})
        serializer.save()


class MealViewSet(viewsets.ModelViewSet):
    serializer_class = MealSerializer

    def get_queryset(self):
        return Meal.objects.filter(user=self.request.user).prefetch_related('items')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FavoriteMealViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteMealSerializer

    def get_queryset(self):
        return FavoriteMeal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        favorite = self.get_object()
        meal_data = {
            'date': date.today(),
            'meal_type': favorite.meal_type,
            'notes': favorite.notes,
            'items': favorite.items,
        }
        serializer = MealSerializer(data=meal_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        meal = serializer.save(user=request.user)
        return Response(MealSerializer(meal).data, status=status.HTTP_201_CREATED)


class BodyEntryViewSet(viewsets.ModelViewSet):
    serializer_class = BodyEntrySerializer

    def get_queryset(self):
        return BodyEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DashboardView(APIView):
    def get(self, request):
        user = request.user
        today = date.today()
        workout = (
            Workout.objects.filter(user=user, date=today)
            .prefetch_related('exercises__exercise')
            .first()
        )
        today_meals = Meal.objects.filter(user=user, date=today)
        nutrition_totals = today_meals.aggregate(
            calories=Sum('items__calories'),
            protein=Sum('items__protein'),
            carbs=Sum('items__carbs'),
            fat=Sum('items__fat'),
        )
        nutrition_totals = {k: v or 0 for k, v in nutrition_totals.items()}
        latest_body = BodyEntry.objects.filter(user=user).order_by('-date').first()
        recent_prs = (
            ExerciseSet.objects.filter(workout_exercise__workout__user=user)
            .values('workout_exercise__exercise__name')
            .annotate(max_weight=Max('weight'), reps=Max('reps'))
            .order_by('-max_weight')[:3]
        )

        streak = 0
        current_date = today
        while Workout.objects.filter(user=user, date=current_date).exists():
            streak += 1
            current_date -= timedelta(days=1)

        latest_workout = Workout.objects.filter(user=user).order_by('-date').first()
        next_planned = None
        if latest_workout:
            if latest_workout.workout_type == 'push':
                next_planned = 'Pull'
            elif latest_workout.workout_type == 'pull':
                next_planned = 'Legs'
            elif latest_workout.workout_type == 'legs':
                next_planned = 'Push'
            else:
                next_planned = 'Full Body'

        return Response({
            'today_workout': WorkoutSerializer(workout).data if workout else None,
            'nutrition': nutrition_totals,
            'current_weight': latest_body.weight if latest_body else None,
            'streak': streak,
            'recent_prs': list(recent_prs),
            'upcoming_workout': next_planned,
        })


class AnalyticsView(APIView):
    def get(self, request):
        user = request.user
        weight_history = (
            BodyEntry.objects.filter(user=user).order_by('date').values('date', 'weight')
        )
        calories_history = (
            Meal.objects.filter(user=user)
            .values('date')
            .annotate(total=Sum('items__calories'))
            .order_by('date')
        )
        protein_history = (
            Meal.objects.filter(user=user)
            .values('date')
            .annotate(total=Sum('items__protein'))
            .order_by('date')
        )
        volume_history = (
            WorkoutExercise.objects.filter(workout__user=user)
            .annotate(
                total_volume=Sum(F('sets__weight') * F('sets__reps'), output_field=FloatField())
            )
            .values('workout__date', 'total_volume')
            .order_by('workout__date')
        )
        frequency = (
            Workout.objects.filter(user=user)
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        return Response({
            'weight': list(weight_history),
            'calories': list(calories_history),
            'protein': list(protein_history),
            'workout_volume': list(volume_history),
            'workout_frequency': list(frequency),
        })


class DietLogViewSet(viewsets.ModelViewSet):
    serializer_class = DietLogSerializer
    lookup_field = 'date'

    def get_queryset(self):
        return DietLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'date parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            diet_log = DietLog.objects.get(user=request.user, date=date_str)
            serializer = self.get_serializer(diet_log)
            return Response(serializer.data)
        except DietLog.DoesNotExist:
            return Response(None)

    def get_object(self):
        date_str = self.kwargs.get('date')
        return DietLog.objects.get_or_create(user=self.request.user, date=date_str)[0]


class DayNoteViewSet(viewsets.ModelViewSet):
    serializer_class = DayNoteSerializer
    pagination_class = None

    def get_queryset(self):
        qs = DayNote.objects.filter(user=self.request.user)
        params = self.request.query_params
        date_exact = params.get('date')
        date_after = params.get('date_after')
        date_before = params.get('date_before')
        reason = params.get('reason')

        if date_exact:
            qs = qs.filter(date=date_exact)
        if date_after:
            qs = qs.filter(date__gte=date_after)
        if date_before:
            qs = qs.filter(date__lte=date_before)
        if reason:
            qs = qs.filter(reason__iexact=reason)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
