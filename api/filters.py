from django_filters import rest_framework as filters
from .models import Workout


class WorkoutFilter(filters.FilterSet):
    date = filters.DateFilter(field_name='date', lookup_expr='exact')
    date_after = filters.DateFilter(field_name='date', lookup_expr='gte')
    date_before = filters.DateFilter(field_name='date', lookup_expr='lte')
    workout_type = filters.CharFilter(field_name='workout_type', lookup_expr='iexact')

    class Meta:
        model = Workout
        fields = ['date', 'date_after', 'date_before', 'workout_type']
