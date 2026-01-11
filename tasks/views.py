from datetime import date, datetime, timedelta
from django.http import JsonResponse
from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Task
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import CustomAuthenticationForm, CustomUserCreationForm, TaskForm
from .models import Task
from .serializers import (
    TaskCompletionSerializer,
    TaskSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


# ============================================================================
# =============================== API VIEWS ==================================
# ============================================================================

class RegisterView(APIView):
    """API endpoint to register a new user."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(ObtainAuthToken):
    """API endpoint to login user and return token."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'message': 'Login successful'
        })


class ApiLogoutView(APIView):
    """API endpoint to logout user by deleting token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        return Response({'message': 'Logout successful'})


class UserProfileView(APIView):
    """API endpoint to view/update/delete current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'user': serializer.data, 'message': 'Profile updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        password = request.data.get('password', '')
        if not request.user.check_password(password):
            return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.delete()
        return Response({'message': 'Account deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class DashboardView(APIView):
    """API endpoint to get user task statistics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(user=request.user)
        stats = {
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(status=Task.STATUS_COMPLETED).count(),
            'pending_tasks': tasks.filter(status=Task.STATUS_PENDING).count(),
            'overdue_tasks': tasks.filter(status=Task.STATUS_OVERDUE).count(),
        }
        return Response({'stats': stats})


class TaskViewSet(viewsets.ModelViewSet):
    """API ViewSet for task CRUD and custom actions."""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        task = self.get_object()
        serializer = TaskCompletionSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(TaskSerializer(task).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        tasks = Task.objects.filter(user=request.user, status=Task.STATUS_OVERDUE)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
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
        tasks = Task.objects.filter(user=request.user, due_date=date.today())
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Task Management API'
    })


# ============================================================================
# ============================= FRONTEND VIEWS ===============================
# ============================================================================

def home(request):
    if request.user.is_authenticated:
        return redirect('task_list')
    return redirect('login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('task_list')

    form = CustomAuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        messages.success(request, 'Login successful!')
        return redirect('task_list')
    elif request.method == 'POST':
        messages.error(request, 'Invalid username or password')
    return render(request, 'tasks/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('task_list')

    form = CustomUserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('task_list')

    return render(request, 'tasks/register.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    messages.info(request, 'Logged out successfully')
    return redirect('login')


@login_required
def dashboard(request):
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
    # Get all tasks for the user
    all_tasks = Task.objects.filter(user=request.user)

    # Count totals
    total_tasks = all_tasks.count()
    completed_count = all_tasks.filter(status=Task.STATUS_COMPLETED).count()

    # Apply filter if any
    filter_type = request.GET.get('filter', '')
    tasks = all_tasks  # start from all tasks
    if filter_type == 'overdue':
        tasks = tasks.filter(status=Task.STATUS_OVERDUE)
    elif filter_type == 'today':
        tasks = tasks.filter(due_date=date.today())
    elif filter_type == 'completed':
        tasks = tasks.filter(status=Task.STATUS_COMPLETED)
    elif filter_type == 'pending':
        tasks = tasks.filter(status=Task.STATUS_PENDING)

    context = {
        'tasks': tasks,
        'filter_type': filter_type,
        'total_tasks': total_tasks,
        'completed_count': completed_count,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def create_task(request):
    form = TaskForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.user = request.user
        task.save()
        messages.success(request, 'Task created successfully!')
        return redirect('task_list')
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Create Task'})


@login_required
def update_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    form = TaskForm(request.POST or None, instance=task)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Task updated successfully!')
        return redirect('task_list')
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Update Task'})


@login_required
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def toggle_task(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if task.status == Task.STATUS_COMPLETED:
        task.mark_as_incomplete()
        messages.success(request, 'Task reopened!')
    else:
        task.mark_as_completed()
        messages.success(request, 'Task completed!')
    return redirect('task_list')


# ============================================================================
# ============================== AJAX ENDPOINTS ==============================
# ============================================================================

@login_required
def get_task_updates(request):
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

    task_data = [
        {
            'id': t.id,
            'title': t.title,
            'priority': t.priority,
            'status': t.status,
            'due_date': str(t.due_date) if t.due_date else None,
            'due_time': str(t.due_time) if t.due_time else None,
            'is_overdue': t.is_overdue(),
            'time_remaining': t.get_time_remaining(),
        }
        for t in tasks
    ]
    return JsonResponse({'tasks': task_data})


@login_required
def get_dashboard_stats(request):
    tasks = Task.objects.filter(user=request.user)
    stats = {
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status=Task.STATUS_COMPLETED).count(),
        'pending_tasks': tasks.filter(status=Task.STATUS_PENDING).count(),
        'overdue_tasks': tasks.filter(status=Task.STATUS_OVERDUE).count(),
    }
    return JsonResponse({'stats': stats})
