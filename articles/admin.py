from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Category, Tag, Article, ArticleImage, Comment

# For Category, we now use DraggableMPTTAdmin for a tree view.
admin.site.register(Category, DraggableMPTTAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 1

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'is_featured', 'is_recommended', 'created_at', 'updated_at')
    list_filter = ('status', 'is_featured', 'is_recommended', 'category')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ArticleImageInline, CommentInline]
    filter_horizontal = ('tags', 'related_articles',)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'name', 'email', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'email', 'content')

admin.site.register(Tag, TagAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
