from django.http import JsonResponse
from .models import Document

def dashboard_api(request):

    documents = Document.objects.all()

    document_list = []

    for doc in documents:
        document_list.append({
            "id": doc.id,
            "title": doc.title,
            "category": doc.category.name if doc.category else "",
            "status": doc.status,
            "owner": doc.owner.username,
        })

    my_documents = Document.objects.filter(
        owner=request.user
    ).count()

    return JsonResponse({
        "summary": {
            "total_documents": Document.objects.count(),
            "my_documents": my_documents,
            "approved": Document.objects.filter(status='approved').count(),
            "pending": Document.objects.filter(status='pending').count(),
            "rejected": Document.objects.filter(status='rejected').count(),
        },
        "documents": document_list
    })