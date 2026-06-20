from django.contrib import admin
from .models import Category, Document, DocumentVersion

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'version', 'owner', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'description')

@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'version_number', 'created_by', 'created_at')
