from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import (
    Department, Employee, LeaveRequest, Attendance,
    PerformanceReview, Training, TrainingParticipant
)
from .serializers import (
    DepartmentSerializer, DepartmentDetailSerializer,
    EmployeeSerializer, EmployeeDetailSerializer,
    LeaveRequestSerializer, AttendanceSerializer,
    PerformanceReviewSerializer, TrainingSerializer,
    TrainingDetailSerializer, TrainingParticipantSerializer
)

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['name', 'code']
    search_fields = ['name', 'code', 'description']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DepartmentDetailSerializer
        return self.serializer_class

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Get all employees in a department"""
        department = self.get_object()
        employees = Employee.objects.filter(department=department)
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['department', 'employment_type', 'employment_status']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id', 'position']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EmployeeDetailSerializer
        return self.serializer_class

    @action(detail=True, methods=['get'])
    def leave_requests(self, request, pk=None):
        """Get all leave requests for an employee"""
        employee = self.get_object()
        leave_requests = LeaveRequest.objects.filter(employee=employee)
        serializer = LeaveRequestSerializer(leave_requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        """Get attendance records for an employee"""
        employee = self.get_object()
        attendance = Attendance.objects.filter(employee=employee)
        serializer = AttendanceSerializer(attendance, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def performance_reviews(self, request, pk=None):
        """Get performance reviews for an employee"""
        employee = self.get_object()
        reviews = PerformanceReview.objects.filter(employee=employee)
        serializer = PerformanceReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def trainings(self, request, pk=None):
        """Get training records for an employee"""
        employee = self.get_object()
        trainings = TrainingParticipant.objects.filter(employee=employee)
        serializer = TrainingParticipantSerializer(trainings, many=True)
        return Response(serializer.data)

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'leave_type', 'status']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a leave request"""
        leave_request = self.get_object()
        if leave_request.status != 'pending':
            return Response(
                {'error': 'Can only approve pending requests'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        leave_request.status = 'approved'
        leave_request.approved_by = request.user.employee
        leave_request.approved_at = timezone.now()
        leave_request.save()
        
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a leave request"""
        leave_request = self.get_object()
        if leave_request.status != 'pending':
            return Response(
                {'error': 'Can only reject pending requests'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        leave_request.status = 'rejected'
        leave_request.save()
        
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'date', 'status']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']

    @action(detail=False, methods=['post'])
    def clock_in(self, request):
        """Record employee clock in"""
        employee = request.user.employee
        date = timezone.now().date()
        
        if Attendance.objects.filter(employee=employee, date=date).exists():
            return Response(
                {'error': 'Already clocked in today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attendance = Attendance.objects.create(
            employee=employee,
            date=date,
            time_in=timezone.now().time()
        )
        
        serializer = self.get_serializer(attendance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def clock_out(self, request):
        """Record employee clock out"""
        employee = request.user.employee
        date = timezone.now().date()
        
        try:
            attendance = Attendance.objects.get(employee=employee, date=date)
        except Attendance.DoesNotExist:
            return Response(
                {'error': 'No clock-in record found for today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attendance.time_out = timezone.now().time()
        attendance.save()
        
        serializer = self.get_serializer(attendance)
        return Response(serializer.data)

class PerformanceReviewViewSet(viewsets.ModelViewSet):
    queryset = PerformanceReview.objects.all()
    serializer_class = PerformanceReviewSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'reviewer', 'review_period']
    search_fields = ['employee__user__first_name', 'employee__user__last_name']

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Employee acknowledges their performance review"""
        review = self.get_object()
        if review.employee.user != request.user:
            return Response(
                {'error': 'Can only acknowledge your own review'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        review.acknowledgement = True
        review.acknowledged_at = timezone.now()
        review.save()
        
        serializer = self.get_serializer(review)
        return Response(serializer.data)

class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']
    search_fields = ['title', 'description', 'trainer']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TrainingDetailSerializer
        return self.serializer_class

    @action(detail=True, methods=['post'])
    def enroll(self, request, pk=None):
        """Enroll an employee in a training program"""
        training = self.get_object()
        employee = request.user.employee
        
        if TrainingParticipant.objects.filter(
            training=training,
            employee=employee
        ).exists():
            return Response(
                {'error': 'Already enrolled in this training'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if (training.participants.count() >= training.max_participants):
            return Response(
                {'error': 'Training is full'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = TrainingParticipant.objects.create(
            training=training,
            employee=employee
        )
        
        serializer = TrainingParticipantSerializer(participant)
        return Response(serializer.data)

class TrainingParticipantViewSet(viewsets.ModelViewSet):
    queryset = TrainingParticipant.objects.all()
    serializer_class = TrainingParticipantSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['training', 'employee', 'status']
    search_fields = ['employee__user__first_name', 'employee__user__last_name', 'training__title']

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark training as completed for a participant"""
        participant = self.get_object()
        score = request.data.get('score')
        feedback = request.data.get('feedback', '')
        
        participant.status = 'completed'
        participant.completion_date = timezone.now().date()
        participant.score = score
        participant.feedback = feedback
        participant.save()
        
        serializer = self.get_serializer(participant)
        return Response(serializer.data)
