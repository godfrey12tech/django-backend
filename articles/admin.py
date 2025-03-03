from django.contrib import admin
from .models import Category, Tag, Article, Comment
from .forms import ArticleAdminForm
from django.forms import Textarea

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = (
        'id', 
        'title', 
        'status', 
        'is_published', 
        'created_at', 
        'updated_at'
    )
    list_filter = ('status', 'is_published', 'category')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags', 'related_articles')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'article', 'name', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('article__title', 'name', 'content')
    ordering = ('-created_at',)
