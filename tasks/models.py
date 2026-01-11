from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, time, date
from django.utils import timezone

class Task(models.Model):
    """
    Task model representing user tasks with deadlines and priorities.
    """
    
    # Priority choices
    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3
    PRIORITY_CRITICAL = 4
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_CRITICAL, 'Critical'),
    ]
    
    # Status choices
    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_OVERDUE = 'overdue'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_OVERDUE, 'Overdue'),
    ]
    
    # Foreign key to user (who owns this task)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='tasks'
    )
    
    # Task details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Priority (1-4, with 4 being highest)
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM,
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    
    # Status (auto-calculated based on completion and dates)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Deadline
    due_date = models.DateField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['priority', 'due_date', 'created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
    
    def save(self, *args, **kwargs):
        """
        Override save to auto-calculate status based on completion and dates.
        """
        # Update status based on completion
        if self.completed_at:
            self.status = self.STATUS_COMPLETED
        elif self.due_date and self.is_overdue():
            self.status = self.STATUS_OVERDUE
        else:
            self.status = self.STATUS_PENDING
        
        super().save(*args, **kwargs)
    
    @property
    def is_completed(self):
        """Check if task is completed."""
        return self.status == self.STATUS_COMPLETED
    
    def is_overdue(self):
        """
        Check if task is overdue (past due date/time and not completed).
        """
        if not self.due_date or self.is_completed:
            return False
        
        today = date.today()
        
        # Check if due date is in the past
        if self.due_date < today:
            return True
        
        # Check if due date is today and time has passed
        if self.due_date == today:
            now = datetime.now().time()
            task_time = self.due_time or time(23, 59, 59)
            return now > task_time
        
        return False
    
    def mark_as_completed(self):
        """Mark task as completed with current timestamp."""
        if not self.completed_at:
            self.completed_at = timezone.now()
            self.save()
    
    def mark_as_incomplete(self):
        """Mark task as incomplete."""
        self.completed_at = None
        self.save()
    
    def get_time_remaining(self):
        """
        Calculate and return time remaining until deadline.
        Returns formatted string or None if no due date.
        """
        if not self.due_date or self.is_completed:
            return None
        
        now = datetime.now()
        due_time = self.due_time or time(23, 59, 59)
        due_datetime = datetime.combine(self.due_date, due_time)
        
        time_diff = due_datetime - now
        
        # If overdue
        if time_diff.total_seconds() < 0:
            return "OVERDUE"
        
        # Calculate days, hours, minutes
        days = time_diff.days
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    @property
    def days_remaining(self):
        """Get number of days remaining (negative for overdue)."""
        if not self.due_date:
            return None
        
        delta = self.due_date - date.today()
        return delta.days