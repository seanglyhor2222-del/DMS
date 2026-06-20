from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpRequest
from .models import Category, Document, DocumentVersion
from datetime import datetime, timedelta
from django.shortcuts import render
from django.db.models import Count
from .models import Document
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Category, Document
from accounts.models import User
import json


category_report = (
    Document.objects
    .values('category__name')
    .annotate(total=Count('id'))
)

from django.db.models import Count
from .models import Document

from django.shortcuts import redirect

def reports(request):
    return redirect('category_reports')


def has_permission(user, document, permission='view'):

    # Everyone can view
    if permission == 'view':
        return True

    # Only owner or admin can edit/delete
    if user.is_superuser:
        return True

    if user == document.owner:
        return True

    return False

@login_required
def document_list(request):
    documents = Document.objects.all().order_by('-created_at')
    mine = request.GET.get('mine')

    if mine == 'true':
        documents = documents.filter(
            owner=request.user
        )
    
    category_id = request.GET.get('category')
    if category_id:
        documents = documents.filter(category_id=category_id)
    
    status = request.GET.get('status')
    if status:
        documents = documents.filter(status=status)
    
    search_query = request.GET.get('search')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Show all documents to everyone
    documents = documents

    for doc in documents:
        if doc.file:
            doc.extension = doc.file.name.split('.')[-1].lower()
        else:
            doc.extension = ''
    
    paginator = Paginator(documents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    all_docs = Document.objects.all()
    
    context = {
        'documents': page_obj,
        'categories': categories,
        'current_category': category_id,
        'current_status': status,
        'search_query': search_query,
        'pending_count': all_docs.filter(status='pending').count(),
        'approved_count': all_docs.filter(status='approved').count(),
        'rejected_count': all_docs.filter(status='rejected').count(),
    }
    return render(request, 'documents/document_list.html', context)

@login_required
def document_upload(request):
    if request.method == 'POST':

        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        file = request.FILES.get('file')
        need_approval = request.POST.get('need_approval')

        if not title or not file:
            messages.error(request, "Title and file are required.")
            return redirect('document_upload')

        # Admin uploads => Auto Approved
        if request.user.is_superuser:

            document = Document.objects.create(
                title=title,
                description=description,
                file=file,
                category_id=category_id if category_id else None,
                owner=request.user,
                status='approved',
                version=1
            )

            messages.success(
                request,
                f"✅ Document '{title}' uploaded and approved automatically."
            )

        # Normal user requests approval
        elif need_approval:

            document = Document.objects.create(
                title=title,
                description=description,
                file=file,
                category_id=category_id if category_id else None,
                owner=request.user,
                status='pending',
                version=1
            )

            from utils.email_notifications import send_new_document_notification
            send_new_document_notification(document)

            messages.info(
                request,
                f"📄 Document '{title}' uploaded and waiting for admin approval."
            )

        # Save as draft
        else:

            document = Document.objects.create(
                title=title,
                description=description,
                file=file,
                category_id=category_id if category_id else None,
                owner=request.user,
                status='draft',
                version=1
            )

            messages.success(
                request,
                f"✅ Document '{title}' saved as draft."
            )

        return redirect(
            'document_detail',
            document_id=document.id
        )

    categories = Category.objects.all()

    return render(
        request,
        'documents/document_upload.html',
        {
            'categories': categories
        }
    )

@login_required
def document_detail(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    
    if not has_permission(request.user, document):
        messages.error(request, "You don't have permission to view this document.")
        return redirect('document_list')
    
    versions = document.versions.all()
    
    context = {
        'document': document,
        'versions': versions,
        'can_edit': has_permission(request.user, document, 'edit'),
        'can_delete': has_permission(request.user, document, 'delete'),
    }
    return render(request, 'documents/document_detail.html', context)

@login_required
def document_edit(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    
    if not has_permission(request.user, document, 'edit') and not request.user.is_superuser:
        messages.error(request, "You don't have permission to edit this document.")
        return redirect('document_detail', document_id=document.id)
    
    if request.method == 'POST':
        new_file = request.FILES.get('file')
        changes = request.POST.get('changes', '')
        
        if new_file:
            DocumentVersion.objects.create(
                document=document,
                version_number=document.version,
                file=document.file,
                changes=changes,
                created_by=request.user
            )
            
            document.file = new_file
            document.version += 1
            document.title = request.POST.get('title', document.title)
            document.description = request.POST.get('description', document.description)
            document.status = 'pending'
            document.save()
            
            messages.success(request, f"Document updated to version {document.version} and submitted for approval.")
        else:
            messages.warning(request, "No new file uploaded.")
        
        return redirect('document_detail', document_id=document.id)
    
    return render(request, 'documents/document_edit.html', {'document': document})

@login_required
def document_delete(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    
    if not has_permission(request.user, document, 'delete') and not request.user.is_superuser:
        messages.error(request, "You don't have permission to delete this document.")
        return redirect('document_detail', document_id=document.id)
    
    if request.method == 'POST':
        title = document.title
        document.delete()
        messages.success(request, f"Document '{title}' has been deleted.")
        return redirect('document_list')
    
    return render(request, 'documents/document_delete_confirm.html', {'document': document})

@login_required
def document_download(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    
    if not has_permission(request.user, document):
        raise Http404("You don't have permission to download this document.")
    
    return FileResponse(document.file, as_attachment=True)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def category_manage(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        Category.objects.create(
            name=name,
            description=description
        )
        
        messages.success(request, f"Category '{name}' created successfully.")
        return redirect('category_manage')
    
    categories = Category.objects.all()
    return render(request, 'documents/category_manage.html', {'categories': categories})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def pending_approvals(request):
    documents = Document.objects.filter(status='pending').order_by('-created_at')
    
    all_docs = Document.objects.all()
    context = {
        'documents': documents,
        'total_documents': all_docs.count(),
        'approved_count': all_docs.filter(status='approved').count(),
        'rejected_count': all_docs.filter(status='rejected').count(),
    }
    return render(request, 'documents/pending_approvals.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def document_approve(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    comment = request.POST.get('comment', '')

    document.status = 'approved'
    document.admin_comment = comment
    document.save()
    
    # Send email notification
    from utils.email_notifications import send_approval_notification
    send_approval_notification(document, 'approved', comment)
    
    messages.success(request, f'✅ Document "{document.title}" has been approved!')
    return redirect('pending_approvals')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def document_reject(request, document_id):

    print("POST DATA =", request.POST)

    document = get_object_or_404(Document, id=document_id)

    comment = request.POST.get('comment', '')

    print("COMMENT =", repr(comment))

    document.status = 'rejected'
    document.admin_comment = comment
    document.save()

    print("AFTER SAVE =", document.admin_comment)

    return redirect('pending_approvals')

from .models import Category, Document

def category_report_detail(request, category_id):

    category = Category.objects.get(
        id=category_id
    )

    documents = Document.objects.filter(
        category=category
    )

    return render(
        request,
        'reports/category_detail.html',
        {
            'category': category,
            'documents': documents
        }
    )

def user_report_detail(request, user_id):

    user = get_object_or_404(
        User,
        user_id=user_id
    )

    documents = Document.objects.filter(
        owner=user
    )

    return render(
        request,
        'reports/user_detail.html',
        {
            'report_user': user,
            'documents': documents
        }
    )

def category_reports(request):

    categories = Category.objects.all()

    search = request.GET.get('search')

    if search:
        categories = categories.filter(
            name__icontains=search
        )

    return render(
        request,
        'reports/category_reports.html',
        {
            'categories': categories
        }
    )

def document_reports(request):

    documents = Document.objects.select_related(
        'category'
    )

    search = request.GET.get('search')

    if search:
        documents = documents.filter(
            title__icontains=search
        )

    return render(
        request,
        'reports/document_reports.html',
        {
            'documents': documents
        }
    )

def user_activity_reports(request):

    users = User.objects.all()

    search = request.GET.get('search')

    if search:
        users = users.filter(
            username__icontains=search
        )

    return render(
        request,
        'reports/user_activity_reports.html',
        {
            'users': users
        }
    )

def user_activity_detail(request, user_id):

    user = get_object_or_404(User,user_id=user_id)

    documents = Document.objects.filter(
        owner=user
    )

    context = {
        'selected_user': user,
        'documents': documents,

        'total_docs': documents.count(),
        'approved_docs': documents.filter(status='approved').count(),
        'pending_docs': documents.filter(status='pending').count(),
        'rejected_docs': documents.filter(status='rejected').count(),
    }

    return render(
        request,
        'reports/user_activity_detail.html',
        context
    )

def dashboard_api(request):

    total_documents = Document.objects.count()

    my_documents = Document.objects.filter(
        owner=request.user
    ).count()

    pending = Document.objects.filter(
        status='pending'
    ).count()

    approved = Document.objects.filter(
        status='approved'
    ).count()

    return JsonResponse({
        'total_documents': total_documents,
        'my_documents': my_documents,
        'pending': pending,
        'approved': approved,
    })