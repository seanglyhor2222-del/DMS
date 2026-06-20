from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from accounts.models import User

def send_approval_notification(document, status, comment=None):
    """
    Send email notification to document owner when approved/rejected
    """
    subject = f'Document "{document.title}" - {status.upper()}'
    
    context = {
        'document': document,
        'status': status,
        'comment': comment,
        'owner': document.owner,
        'site_url': 'http://127.0.0.1:8000',
    }
    
    html_message = render_to_string('emails/approval_notification.html', context)
    plain_message = strip_tags(html_message)
    
    # Send to document owner
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[document.owner.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✅ Email sent to {document.owner.email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def send_new_document_notification(document):
    """
    Send notification to all admins and managers when document is uploaded
    """
    subject = f'New Document Uploaded: "{document.title}"'
    
    context = {
        'document': document,
        'uploader': document.owner,
        'site_url': 'http://127.0.0.1:8000',
    }
    
    html_message = render_to_string('emails/new_document_notification.html', context)
    plain_message = strip_tags(html_message)
    
    # Get all admin and manager emails
    admin_emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
    manager_emails = User.objects.filter(role__role_name='manager', is_active=True).values_list('email', flat=True)
    
    # Combine emails
    all_recipients = list(admin_emails) + list(manager_emails)
    
    # Remove duplicates and empty emails
    all_recipients = list(set([email for email in all_recipients if email]))
    
    if all_recipients:
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=all_recipients,
                html_message=html_message,
                fail_silently=False,
            )
            print(f"✅ New document notification sent to {len(all_recipients)} recipients")
            return True
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    else:
        print("⚠️ No admin/manager emails found")
        return False

def send_bulk_notification_to_users(users, subject, message):
    """
    Send notification to multiple users
    """
    emails = [user.email for user in users if user.email]
    
    if emails:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                fail_silently=False,
            )
            print(f"✅ Bulk notification sent to {len(emails)} users")
            return True
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    return False

def send_welcome_email(user):
    """
    Send welcome email when user registers
    """
    subject = f'Welcome to DMS System, {user.username}!'
    
    context = {
        'user': user,
        'site_url': 'http://127.0.0.1:8000',
    }
    
    html_message = render_to_string('emails/welcome_email.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✅ Welcome email sent to {user.email}")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def send_activity_summary_email(user, activities):
    """
    Send daily/weekly activity summary to user
    """
    subject = f'Your Document Activity Summary'
    
    context = {
        'user': user,
        'activities': activities,
        'site_url': 'http://127.0.0.1:8000',
        'count': len(activities),
    }
    
    html_message = render_to_string('emails/activity_summary.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False
