from django_filters import rest_framework as filters
from .models import Workout

class WorkoutFilter(filters.FilterSet):
    date = filters.DateFilter(field_name='date', lookup_expr='exact')
    split = filters.CharFilter(field_name='split', lookup_expr='iexact')

    class Meta:
        model = Workout
        fields = ['date', 'split']
