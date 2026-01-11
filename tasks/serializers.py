from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from .models import Task
from datetime import datetime

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields don't match."})
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password2')  # Remove confirmation field
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read-only).
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = ['username', 'email']
    
    def validate_username(self, value):
        """Ensure username is unique (excluding current user)."""
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_email(self, value):
        """Ensure email is unique (excluding current user)."""
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    """
    time_remaining = serializers.SerializerMethodField(read_only=True)
    is_overdue = serializers.SerializerMethodField(read_only=True)
    days_remaining = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'priority',
            'status',
            'due_date',
            'due_time',
            'created_at',
            'updated_at',
            'completed_at',
            'time_remaining',
            'is_overdue',
            'days_remaining',
        ]
        read_only_fields = [
            'id',
            'status',
            'created_at',
            'updated_at',
            'completed_at',
            'time_remaining',
            'is_overdue',
            'days_remaining',
        ]
    
    def get_time_remaining(self, obj):
        """Get formatted time remaining."""
        return obj.get_time_remaining()
    
    def get_is_overdue(self, obj):
        """Check if task is overdue."""
        return obj.is_overdue()
    
    def get_days_remaining(self, obj):
        """Get days remaining."""
        return obj.days_remaining
    
    def validate_due_date(self, value):
        """Validate that due date is not in the past."""
        if value and value < datetime.now().date():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value
    
    def create(self, validated_data):
        """Create task and assign to current user."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        Update task with custom logic.
        Prevent editing of completed tasks.
        """
        if instance.is_completed:
            raise serializers.ValidationError(
                "Cannot edit a completed task. Mark it as incomplete first."
            )
        
        return super().update(instance, validated_data)

class TaskCompletionSerializer(serializers.Serializer):
    """
    Serializer for marking tasks as complete/incomplete.
    """
    completed = serializers.BooleanField(required=True)
    
    def update(self, instance, validated_data):
        """Mark task as complete or incomplete."""
        if validated_data['completed']:
            instance.mark_as_completed()
        else:
            instance.mark_as_incomplete()
        return instance