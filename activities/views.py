from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ActivityLog
from accounts.models import User

@login_required
@user_passes_test(lambda u: u.is_superuser)
def activity_log(request):
    """View all activities for admin (all users)"""
    # Get all activities, ordered by latest first
    activities = ActivityLog.objects.all().order_by('-timestamp')
    
    # Get filter parameters
    user_filter = request.GET.get('user')
    action_filter = request.GET.get('action')
    
    # Apply filters
    if user_filter:
        activities = activities.filter(user_id=user_filter)
    if action_filter:
        activities = activities.filter(action=action_filter)
    
    # Get unique users for filter dropdown
    users = User.objects.all().order_by('username')
    
    # Get unique actions for filter dropdown
    actions = ActivityLog.objects.values_list('action', flat=True).distinct()
    
    context = {
        'activities': activities,
        'users': users,
        'actions': actions,
        'selected_user': user_filter,
        'selected_action': action_filter,
    }
    return render(request, 'activities/activity_log.html', context)
