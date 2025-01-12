from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'employees', views.EmployeeViewSet)
router.register(r'leave-requests', views.LeaveRequestViewSet)
router.register(r'attendance', views.AttendanceViewSet)
router.register(r'performance-reviews', views.PerformanceReviewViewSet)
router.register(r'trainings', views.TrainingViewSet)
router.register(r'training-participants', views.TrainingParticipantViewSet)

app_name = 'hr_management'

urlpatterns = [
    path('', include(router.urls)),
]
