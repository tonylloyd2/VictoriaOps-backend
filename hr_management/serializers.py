from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Department, Employee, LeaveRequest, Attendance,
    PerformanceReview, Training, TrainingParticipant
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Employee
        fields = ['id', 'user', 'department', 'department_name', 'position', 'hire_date', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        employee = Employee.objects.create(user=user, **validated_data)
        return employee

    def update(self, instance, validated_data):
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        return super().update(instance, validated_data)

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.user.get_full_name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'approved_at']

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class PerformanceReviewSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.user.get_full_name', read_only=True)

    class Meta:
        model = PerformanceReview
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'acknowledged_at']

class TrainingSerializer(serializers.ModelSerializer):
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Training
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_participant_count(self, obj):
        return obj.participants.count()

class TrainingParticipantSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)
    training_title = serializers.CharField(source='training.title', read_only=True)

    class Meta:
        model = TrainingParticipant
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'enrollment_date']

# Nested Serializers for detailed views
class EmployeeDetailSerializer(EmployeeSerializer):
    leave_requests = LeaveRequestSerializer(many=True, read_only=True)
    attendance = AttendanceSerializer(many=True, read_only=True)
    performance_reviews = PerformanceReviewSerializer(many=True, read_only=True)
    trainings = TrainingParticipantSerializer(many=True, read_only=True, source='trainingparticipant_set')

    class Meta(EmployeeSerializer.Meta):
        fields = list(EmployeeSerializer.Meta.fields) + ['leave_requests', 'attendance', 'performance_reviews', 'trainings']

class DepartmentDetailSerializer(DepartmentSerializer):
    manager = EmployeeSerializer(read_only=True)
    employees = EmployeeSerializer(many=True, read_only=True, source='employee_set')

    class Meta(DepartmentSerializer.Meta):
        fields = list(DepartmentSerializer.Meta.fields) + ['employees']

class TrainingDetailSerializer(TrainingSerializer):
    participants = TrainingParticipantSerializer(
        many=True,
        read_only=True,
        source='trainingparticipant_set'
    )

    class Meta(TrainingSerializer.Meta):
        fields = list(TrainingSerializer.Meta.fields) + ['participants']
