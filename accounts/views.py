from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from django.contrib.sessions.models import Session
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from documents.models import Document, Category
from .models import User, Role
from activities.models import ActivityLog
from .models import UserSession

def get_device_info(request):
    """Get device/browser information from request"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    if 'Android' in user_agent:
        os = 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        os = 'iOS'
    elif 'Windows' in user_agent:
        os = 'Windows'
    elif 'Mac' in user_agent:
        os = 'macOS'
    elif 'Linux' in user_agent:
        os = 'Linux'
    else:
        os = 'Unknown OS'
    
    if 'Chrome' in user_agent and 'Edg' not in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
        browser = 'Safari'
    elif 'Edg' in user_agent:
        browser = 'Edge'
    elif 'Opera' in user_agent:
        browser = 'Opera'
    else:
        browser = 'Unknown Browser'
    
    return f"{browser} on {os}"

@login_required
def dashboard(request):
    documents = Document.objects.all()
    
    if not request.user.is_superuser:
        documents = documents.filter(owner=request.user)
    
    total_documents = documents.count()
    my_documents = Document.objects.filter(owner=request.user).count()
    approved_count = documents.filter(status='approved').count()
    pending_count = documents.filter(status='pending').count()
    rejected_count = documents.filter(status='rejected').count()
    draft_count = documents.filter(status='draft').count()
    
    total = total_documents if total_documents > 0 else 1
    approved_percentage = round((approved_count / total) * 100, 1)
    pending_percentage = round((pending_count / total) * 100, 1)
    rejected_percentage = round((rejected_count / total) * 100, 1)
    draft_percentage = round((draft_count / total) * 100, 1)
    
    recent_documents = documents.order_by('-created_at')[:10]
    
    categories = Category.objects.annotate(doc_count=Count('document'))
    for cat in categories:
        cat.percentage = round((cat.doc_count / total) * 100, 1) if total > 0 else 0
    
    top_users = User.objects.annotate(doc_count=Count('document')).order_by('-doc_count')[:5]
    max_docs = top_users[0].doc_count if top_users else 1
    for user in top_users:
        user.percentage = round((user.doc_count / max_docs) * 100, 1) if max_docs > 0 else 0
    
    today = datetime.now().date()
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        chart_labels.append(date.strftime('%b %d'))
        count = documents.filter(created_at__date=date).count()
        chart_data.append(count)
    
    context = {
        'total_documents': total_documents,
        'my_documents': my_documents,
        'approved_count': approved_count,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
        'draft_count': draft_count,
        'approved_percentage': approved_percentage,
        'pending_percentage': pending_percentage,
        'rejected_percentage': rejected_percentage,
        'draft_percentage': draft_percentage,
        'recent_documents': recent_documents,
        'categories': categories,
        'top_users': top_users,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'user': request.user,
    }
    return render(request, 'dashboard.html', context)

# ==================== Profile View ====================

@login_required
def profile_view(request):
    # Update profile
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.department = request.POST.get('department', '')
        
        # Change password if provided
        new_password = request.POST.get('password', '')
        if new_password:
            user.set_password(new_password)
            user.save()

            sessions = UserSession.objects.filter(user=user)

            for s in sessions:
                Session.objects.filter(
                    session_key=s.session_key
                ).delete()

            sessions.delete()

            logout(request)

            messages.success(
                request,
                "Password changed successfully. Please login again."
            )

            return redirect('login')
        
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
    
    # Get user activities
    activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')
    
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    user_documents = Document.objects.filter(owner=request.user)
    total_documents = user_documents.count()
    pending_documents = user_documents.filter(status='pending').count()
    approved_documents = user_documents.filter(status='approved').count()
    
    context = {
        'user_activities': page_obj,
        'total_documents': total_documents,
        'pending_documents': pending_documents,
        'approved_documents': approved_documents,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)

# ==================== User Management Views ====================

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if username and email and password:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            messages.success(request, f'User "{username}" created successfully!')
            return redirect('user_list')
        else:
            messages.error(request, "Please fill in all required fields.")
    
    return render(request, 'accounts/user_form.html', {'title': 'Create New User'})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_edit(request, user_id):
    user = get_object_or_404(User, user_id=user_id)
    
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.is_active = request.POST.get('is_active') == 'on'
        
        if request.POST.get('password'):
            user.set_password(request.POST.get('password'))
        
        user.save()
        messages.success(request, f'User "{user.username}" updated successfully!')
        return redirect('user_list')
    
    return render(request, 'accounts/user_edit.html', {'edit_user': user})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_delete(request, user_id):
    user = get_object_or_404(User, user_id=user_id)
    
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, "You cannot delete your own account!")
        else:
            username = user.username
            user.delete()
            messages.success(request, f'User "{username}" deleted successfully!')
        return redirect('user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

# ==================== Registration View ====================

from .forms import UserRegistrationForm

def logout_view(request):
    if request.user.is_authenticated:

        device_info = get_device_info(request)

        if request.session.session_key:

            Session.objects.filter(
                session_key=request.session.session_key
            ).delete()

            UserSession.objects.filter(
                session_key=request.session.session_key
            ).delete()

        ActivityLog.objects.create(
            user=request.user,
            action='logout',
            description=f'User {request.user.username} logged out from {device_info}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        logout(request)

    return redirect('login')

# ==================== Session Management Views ====================

@login_required
def active_sessions(request):
    """View all active sessions for the current user"""
    sessions = UserSession.objects.filter(user=request.user, is_active=True).order_by('-last_activity')
    
    # Get current session key
    current_session = request.session.session_key
    
    context = {
        'sessions': sessions,
        'current_session': current_session,
    }
    return render(request, 'accounts/active_sessions.html', context)

@login_required
def force_logout_session(request, session_key):
    """Force logout a specific session"""

    if request.method == 'POST':

        session = get_object_or_404(
            UserSession,
            session_key=session_key,
            user=request.user
        )

        device_name = session.device_info

        # Delete Django session
        Session.objects.filter(
            session_key=session.session_key
        ).delete()

        # Delete UserSession record
        session.delete()

        ActivityLog.objects.create(
            user=request.user,
            action='force_logout',
            description=f'User {request.user.username} force logged out session from {device_name}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # If current device
        if session_key == request.session.session_key:
            logout(request)
            messages.warning(
                request,
                "You have been logged out."
            )
            return redirect('login')

        messages.success(
            request,
            f"Successfully logged out {device_name}"
        )

    return redirect('active_sessions')

@login_required
def force_logout_all_sessions(request):
    """Force logout all sessions except current"""
    if request.method == 'POST':
        current_session = request.session.session_key
        
        other_sessions = UserSession.objects.filter(
            user=request.user
        ).exclude(
            session_key=current_session
        )

        count = other_sessions.count()

        for s in other_sessions:
            Session.objects.filter(
                session_key=s.session_key
            ).delete()

            s.delete()
        
        # Record activity
        ActivityLog.objects.create(
            user=request.user,
            action='force_logout',
            description=f'User {request.user.username} force logged out {count} other session(s)',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f"Successfully logged out {count} other session(s)")
    
    return redirect('active_sessions')

@login_required
def change_password_and_logout_all(request):
    """Change password and logout all sessions"""
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('active_sessions')
        
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters!")
            return redirect('active_sessions')
        
        # Change password
        user = request.user
        user.set_password(new_password)
        user.save()
        
        # Delete all sessions
        sessions = UserSession.objects.filter(user=user)

        for s in sessions:
            Session.objects.filter(
                session_key=s.session_key
            ).delete()

        sessions.delete()
        
        # Record activity
        ActivityLog.objects.create(
            user=user,
            action='force_logout',
            description=f'User {user.username} changed password and logged out all devices',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Logout current user
        logout(request)
        
        messages.success(request, "Password changed successfully! Please login with your new password.")
        return redirect('login')
    
    return redirect('active_sessions')

# ==================== Google Login ====================

from django.shortcuts import redirect

def google_login(request):
    return redirect('/accounts/google/login/?process=login')

from utils.email_notifications import send_welcome_email

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            device_info = get_device_info(request)
            
            ActivityLog.objects.create(
                user=user,
                action='register',
                description=f'New user {user.username} registered from {device_info}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Send welcome email
            send_welcome_email(user)
            
            messages.success(request, f'Account created successfully! You can now login.')
            return redirect('login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

# ==================== 2FA Views ====================

import pyotp
import qrcode
from io import BytesIO
import base64

@login_required
def setup_2fa(request):
    """Setup Two-Factor Authentication"""
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'enable':
            code = request.POST.get('code')
            if user.verify_otp(code):
                user.enable_2fa()
                messages.success(request, "✅ Two-Factor Authentication enabled successfully!")
                return redirect('profile')
            else:
                messages.error(request, "❌ Invalid verification code. Please try again.")
        
        elif action == 'disable':
            user.disable_2fa()
            messages.success(request, "✅ Two-Factor Authentication disabled successfully!")
            return redirect('profile')
    
    # Generate OTP secret if not exists
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        user.save()
    
    # Generate QR code
    otp_uri = user.get_otp_uri()
    
    # Create QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(otp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for display
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'qr_code': qr_code_base64,
        'otp_secret': user.otp_secret,
        'otp_enabled': user.otp_enabled,
    }
    return render(request, 'accounts/setup_2fa.html', context)


def verify_2fa(request):
    """Verify 2FA code during login"""
    if request.method == 'POST':
        code = request.POST.get('code')
        user_id = request.session.get('2fa_user_id')
        
        if not user_id:
            return redirect('login')
        
        from accounts.models import User
        try:
            user = User.objects.get(user_id=user_id)  # កែពី id=user_id ទៅ user_id=user_id
            if user.verify_otp(code):
                # Clear 2fa session
                del request.session['2fa_user_id']
                # Login the user
                from django.contrib.auth import login
                login(request, user)

                if not request.session.session_key:
                    request.session.save()

                print("=" * 50)
                print("USER:", user.username)
                print("SESSION:", request.session.session_key)

                device_info = get_device_info(request)

                session, created = UserSession.objects.update_or_create(
                    session_key=request.session.session_key,
                    defaults={
                        'user': user,
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'device_info': device_info,
                        'is_active': True,
                    }
                )

                print("SESSION ID:", session.id)
                print("CREATED:", created)
                
                # Record activity
                from activities.models import ActivityLog
                ActivityLog.objects.create(
                    user=user,
                    action='login',
                    description=f'User {user.username} logged in with 2FA',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('dashboard')
            else:
                messages.error(request, "❌ Invalid verification code!")
        except User.DoesNotExist:
            pass
    
    return render(request, 'accounts/verify_2fa.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if 2FA is enabled
            if user.otp_enabled:
                # Store user id in session and redirect to 2FA verification
                request.session['2fa_user_id'] = user.user_id  # កែពី user.id ទៅ user.user_id
                return redirect('verify_2fa')
            else:
                login(request, user)

                if not request.session.session_key:
                    request.session.save()

                device_info = get_device_info(request)

                UserSession.objects.update_or_create(
                    session_key=request.session.session_key,
                    defaults={
                        'user': user,
                        'ip_address': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'device_info': device_info,
                        'is_active': True,
                    }
                )
                
                ActivityLog.objects.create(
                    user=user,
                    action='login',
                    description=f'User {user.username} logged in from {device_info}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('dashboard')
        else:
            messages.error(request, "❌Invalid username or password.")
    
    return render(request, 'registration/login.html')