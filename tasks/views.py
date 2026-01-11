from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime, timedelta, date
from .forms import CustomUserCreationForm, CustomAuthenticationForm, TaskForm

from .models import Task
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
    TaskSerializer,
    TaskCompletionSerializer,
)

# ============================================================================
# API VIEWS (REST API endpoints at /api/*)
# ============================================================================

class RegisterView(APIView):
    """Register a new user. URL: /api/register/"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(ObtainAuthToken):
    """Login user and return token. URL: /api/login/"""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'message': 'Login successful'
        })


class ApiLogoutView(APIView):
    """API logout (deletes token). URL: /api/logout/"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
        except (AttributeError, Token.DoesNotExist):
            pass
        return Response({'message': 'Logout successful'})


class UserProfileView(APIView):
    """Get/update user profile. URL: /api/users/profile/"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user profile."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user profile."""
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'user': serializer.data,
                'message': 'Profile updated successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """Delete user account."""
        password = request.data.get('password', '')
        
        if not request.user.check_password(password):
            return Response(
                {'error': 'Incorrect password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request.user.delete()
        return Response({
            'message': 'Account deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)


class DashboardView(APIView):
    """Get dashboard statistics. URL: /api/dashboard/"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_tasks = Task.objects.filter(user=request.user)
        
        stats = {
            'total_tasks': user_tasks.count(),
            'completed_tasks': user_tasks.filter(status=Task.STATUS_COMPLETED).count(),
            'pending_tasks': user_tasks.filter(status=Task.STATUS_PENDING).count(),
            'overdue_tasks': user_tasks.filter(status=Task.STATUS_OVERDUE).count(),
        }
        
        return Response({'stats': stats})


class TaskViewSet(viewsets.ModelViewSet):
    """
    Task CRUD operations. URLs:
    - GET/POST /api/tasks/ - List/Create tasks
    - GET/PUT/PATCH/DELETE /api/tasks/{id}/ - Retrieve/Update/Delete
    - PATCH /api/tasks/{id}/complete/ - Mark complete/incomplete
    - GET /api/tasks/overdue/ - Overdue tasks
    - GET /api/tasks/upcoming/ - Upcoming tasks
    - GET /api/tasks/today/ - Today's tasks
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return tasks for current user."""
        return Task.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user when creating a task."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        """Mark task as complete/incomplete."""
        task = self.get_object()
        serializer = TaskCompletionSerializer(
            task,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(TaskSerializer(task).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks."""
        tasks = Task.objects.filter(
            user=request.user,
            status=Task.STATUS_OVERDUE
        )
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get tasks due in next 7 days."""
        next_week = date.today() + timedelta(days=7)
        tasks = Task.objects.filter(
            user=request.user,
            status=Task.STATUS_PENDING,
            due_date__range=[date.today(), next_week]
        ).order_by('due_date')
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's tasks."""
        tasks = Task.objects.filter(
            user=request.user,
            due_date=date.today()
        )
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint. URL: /api/health/"""
    return Response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Task Management API'
    })


# ============================================================================
# FRONTEND VIEWS (Traditional Django views at root URLs)
# ============================================================================

def home(request):
    """Home page. URL: /"""
    if request.user.is_authenticated:
        return redirect('/tasks/')
    return redirect('login')


def login_view(request):
    """Login page. URL: /login/"""
    if request.user.is_authenticated:
        return redirect('/tasks/')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('/tasks/')
        else:
            messages.error(request, 'Invalid username or password')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'tasks/login.html', {'form': form})


def register_view(request):
    """Registration page. URL: /register/"""
    if request.user.is_authenticated:
        return redirect('/tasks/')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('/tasks/')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'tasks/register.html', {'form': form})


def logout_view(request):
    """Logout page. URL: /logout/"""
    auth_logout(request)
    messages.info(request, 'Logged out successfully')
    return redirect('login')


@login_required
def dashboard(request):
    """Dashboard page. URL: /dashboard/"""
    tasks = Task.objects.filter(user=request.user)
    
    stats = {
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status=Task.STATUS_COMPLETED).count(),
        'pending_tasks': tasks.filter(status=Task.STATUS_PENDING).count(),
        'overdue_tasks': tasks.filter(status=Task.STATUS_OVERDUE).count(),
    }
    
    return render(request, 'tasks/dashboard.html', {'stats': stats})


@login_required
def task_list(request):
    """Task list page. URL: /tasks/"""
    tasks = Task.objects.filter(user=request.user)
    
    # Apply filters
    filter_type = request.GET.get('filter', '')
    
    if filter_type == 'overdue':
        tasks = tasks.filter(status=Task.STATUS_OVERDUE)
    elif filter_type == 'today':
        tasks = tasks.filter(due_date=date.today())
    elif filter_type == 'completed':
        tasks = tasks.filter(status=Task.STATUS_COMPLETED)
    elif filter_type == 'pending':
        tasks = tasks.filter(status=Task.STATUS_PENDING)
    
    return render(request, 'tasks/task_list.html', {
        'tasks': tasks,
        'filter_type': filter_type,
    })


@login_required
def create_task(request):
    """Create task page. URL: /tasks/create/"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Task created successfully!')
            return redirect('/tasks/')
    else:
        form = TaskForm()
    
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Create Task'
    })


@login_required
def update_task(request, pk):
    """Update task page. URL: /tasks/<pk>/update/"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('/tasks/')
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'title': 'Update Task'
    })


@login_required
def delete_task(request, pk):
    """Delete task page. URL: /tasks/<pk>/delete/"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('/tasks/')
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def toggle_task(request, pk):
    """Toggle task completion. URL: /tasks/<pk>/toggle/"""
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if task.status == Task.STATUS_COMPLETED:
        task.mark_as_incomplete()
        messages.success(request, 'Task reopened!')
    else:
        task.mark_as_completed()
        messages.success(request, 'Task completed!')
    
    return redirect('/tasks/')

# ============================================================================
# AJAX ENDPOINTS (For real-time updates without page reload)
# ============================================================================

@login_required
def get_task_updates(request):
    """AJAX endpoint for task updates. URL: /api/task-updates/"""
    tasks = Task.objects.filter(user=request.user)
    
    filter_type = request.GET.get('filter', '')
    if filter_type == 'overdue':
        tasks = tasks.filter(status=Task.STATUS_OVERDUE)
    elif filter_type == 'today':
        tasks = tasks.filter(due_date=date.today())
    elif filter_type == 'completed':
        tasks = tasks.filter(status=Task.STATUS_COMPLETED)
    elif filter_type == 'pending':
        tasks = tasks.filter(status=Task.STATUS_PENDING)
    
    task_data = []
    for task in tasks:
        task_data.append({
            'id': task.id,
            'title': task.title,
            'priority': task.priority,
            'status': task.status,
            'due_date': str(task.due_date) if task.due_date else None,
            'due_time': str(task.due_time) if task.due_time else None,
            'is_overdue': task.is_overdue(),
            'time_remaining': task.get_time_remaining(),
        })
    
    return JsonResponse({'tasks': task_data})


@login_required
def get_dashboard_stats(request):
    """AJAX endpoint for dashboard stats. URL: /api/dashboard-stats/"""
    tasks = Task.objects.filter(user=request.user)
    
    stats = {
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status=Task.STATUS_COMPLETED).count(),
        'pending_tasks': tasks.filter(status=Task.STATUS_PENDING).count(),
        'overdue_tasks': tasks.filter(status=Task.STATUS_OVERDUE).count(),
    }
    
    return JsonResponse({'stats': stats})