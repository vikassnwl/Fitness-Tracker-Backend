from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .auth_views import LoginView, LogoutView, MeView, RegisterView
from .views import (
    ExerciseViewSet, SplitDayExerciseViewSet, WorkoutViewSet, WorkoutExerciseViewSet, ExerciseSetViewSet,
    MealViewSet, FavoriteMealViewSet, BodyEntryViewSet, DietLogViewSet, DashboardView, AnalyticsView
)

router = DefaultRouter()
router.register('exercises', ExerciseViewSet, basename='exercise')
router.register('split-day-exercises', SplitDayExerciseViewSet, basename='split-day-exercise')
router.register('workouts', WorkoutViewSet, basename='workout')
router.register('workout-exercises', WorkoutExerciseViewSet, basename='workout-exercise')
router.register('exercise-sets', ExerciseSetViewSet, basename='exercise-set')
router.register('meals', MealViewSet, basename='meal')
router.register('favorite-meals', FavoriteMealViewSet, basename='favorite-meal')
router.register('body-entries', BodyEntryViewSet, basename='body-entry')
router.register('diet-logs', DietLogViewSet, basename='diet-log')

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('', include(router.urls)),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
]
