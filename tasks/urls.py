from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API Router
router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='api-task')  # Keep basename

urlpatterns = [
    # ========== FRONTEND URLs MUST COME FIRST! ==========
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ⚠️ FRONTEND TASK URL - MUST BE BEFORE API INCLUDE!
    path('tasks/', views.task_list, name='task_list'),
    
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:pk>/update/', views.update_task, name='update_task'),
    path('tasks/<int:pk>/delete/', views.delete_task, name='delete_task'),
    path('tasks/<int:pk>/toggle/', views.toggle_task, name='toggle_task'),
    
    # AJAX URLs
    path('ajax/task-updates/', views.get_task_updates, name='task_updates'),
    path('ajax/dashboard-stats/', views.get_dashboard_stats, name='dashboard_stats'),
    
    # ========== API URLs COME AFTER ==========
    path('register/', views.RegisterView.as_view(), name='api-register'),
    path('login/', views.LoginView.as_view(), name='api-login'),
    path('logout/', views.ApiLogoutView.as_view(), name='api-logout'),
    path('users/profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('dashboard/', views.DashboardView.as_view(), name='api-dashboard'),
    path('health/', views.health_check, name='health-check'),
    
     #⚠️ API ROUTER - MUST COME AFTER FRONTEND!
    path('', include(router.urls)),
]