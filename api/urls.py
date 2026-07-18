from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .auth_views import LoginView, LogoutView, MeView, RegisterView
from .views import (
    ExerciseViewSet, WorkoutViewSet, WorkoutExerciseViewSet, ExerciseSetViewSet,
    MealViewSet, FavoriteMealViewSet, BodyEntryViewSet, DietLogViewSet, DashboardView, AnalyticsView
)

router = DefaultRouter()
router.register('exercises', ExerciseViewSet)
router.register('workouts', WorkoutViewSet)
router.register('workout-exercises', WorkoutExerciseViewSet)
router.register('exercise-sets', ExerciseSetViewSet)
router.register('meals', MealViewSet)
router.register('favorite-meals', FavoriteMealViewSet)
router.register('body-entries', BodyEntryViewSet)
router.register('diet-logs', DietLogViewSet)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('', include(router.urls)),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
]
