from datetime import date, timedelta
from django.db.models import Count, FloatField, Max, Sum, F, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Exercise, Workout, WorkoutExercise, ExerciseSet, Meal, MealItem, FavoriteMeal, BodyEntry, DietLog
from .serializers import (
    ExerciseSerializer, WorkoutSerializer, WorkoutExerciseSerializer,
    ExerciseSetSerializer, MealSerializer, FavoriteMealSerializer, BodyEntrySerializer, DietLogSerializer
)

class ExerciseViewSet(viewsets.ModelViewSet):
    queryset = Exercise.objects.all().order_by('name')
    serializer_class = ExerciseSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])
        exercises = Exercise.objects.filter(
            Q(name__icontains=query) | Q(muscle_group__icontains=query)
        ).order_by('name')[:20]
        serializer = self.get_serializer(exercises, many=True)
        return Response(serializer.data)

class WorkoutViewSet(viewsets.ModelViewSet):
    queryset = Workout.objects.prefetch_related('exercises__sets').all()
    serializer_class = WorkoutSerializer

class WorkoutExerciseViewSet(viewsets.ModelViewSet):
    queryset = WorkoutExercise.objects.prefetch_related('sets').all()
    serializer_class = WorkoutExerciseSerializer

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Accepts: [{"id": 1, "order": 0}, {"id": 2, "order": 1}, ...]
        Updates order for each WorkoutExercise.
        """
        items = request.data
        if not isinstance(items, list):
            return Response({'error': 'Expected a list'}, status=status.HTTP_400_BAD_REQUEST)
        for item in items:
            WorkoutExercise.objects.filter(id=item['id']).update(order=item['order'])
        return Response({'status': 'ok'})

class ExerciseSetViewSet(viewsets.ModelViewSet):
    queryset = ExerciseSet.objects.all()
    serializer_class = ExerciseSetSerializer

class MealViewSet(viewsets.ModelViewSet):
    queryset = Meal.objects.prefetch_related('items').all()
    serializer_class = MealSerializer

class FavoriteMealViewSet(viewsets.ModelViewSet):
    queryset = FavoriteMeal.objects.all()
    serializer_class = FavoriteMealSerializer

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        favorite = self.get_object()
        meal_data = {
            'date': date.today(),
            'meal_type': favorite.meal_type,
            'notes': favorite.notes,
            'items': favorite.items,
        }
        serializer = MealSerializer(data=meal_data)
        serializer.is_valid(raise_exception=True)
        meal = serializer.save()
        return Response(MealSerializer(meal).data, status=status.HTTP_201_CREATED)

class BodyEntryViewSet(viewsets.ModelViewSet):
    queryset = BodyEntry.objects.all()
    serializer_class = BodyEntrySerializer

class DashboardView(APIView):
    def get(self, request):
        today = date.today()
        workout = Workout.objects.filter(date=today).prefetch_related('exercises__exercise').first()
        today_meals = Meal.objects.filter(date=today)
        nutrition_totals = today_meals.aggregate(
            calories=Sum('items__calories'),
            protein=Sum('items__protein'),
            carbs=Sum('items__carbs'),
            fat=Sum('items__fat'),
        )
        nutrition_totals = {k: v or 0 for k, v in nutrition_totals.items()}
        latest_body = BodyEntry.objects.order_by('-date').first()
        recent_prs = ExerciseSet.objects.values('workout_exercise__exercise__name').annotate(
            max_weight=Max('weight'),
            reps=Max('reps')
        ).order_by('-max_weight')[:3]

        streak = 0
        current_date = today
        while Workout.objects.filter(date=current_date).exists():
            streak += 1
            current_date -= timedelta(days=1)

        latest_workout = Workout.objects.order_by('-date').first()
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
        weight_history = BodyEntry.objects.order_by('date').values('date', 'weight')
        calories_history = Meal.objects.values('date').annotate(total=Sum('items__calories')).order_by('date')
        protein_history = Meal.objects.values('date').annotate(total=Sum('items__protein')).order_by('date')
        volume_history = WorkoutExercise.objects.annotate(
            total_volume=Sum(F('sets__weight') * F('sets__reps'), output_field=FloatField())
        ).values('workout__date', 'total_volume').order_by('workout__date')
        frequency = Workout.objects.values('date').annotate(count=Count('id')).order_by('date')
        return Response({
            'weight': list(weight_history),
            'calories': list(calories_history),
            'protein': list(protein_history),
            'workout_volume': list(volume_history),
            'workout_frequency': list(frequency),
        })

class DietLogViewSet(viewsets.ModelViewSet):
    queryset = DietLog.objects.all()
    serializer_class = DietLogSerializer
    lookup_field = 'date'

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'date parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            diet_log = DietLog.objects.get(date=date_str)
            serializer = self.get_serializer(diet_log)
            return Response(serializer.data)
        except DietLog.DoesNotExist:
            return Response(None)

    def get_object(self):
        date_str = self.kwargs.get('date')
        return DietLog.objects.get_or_create(date=date_str)[0]
