from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from mptt.admin import DraggableMPTTAdmin
from .models import User, Category, Tag, Article, ArticleImage, Comment
from .forms import CategoryAdminForm, ArticleAdminForm

# Custom UserAdmin to include the role field.
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_display = BaseUserAdmin.list_display + ('role',)
    list_filter = BaseUserAdmin.list_filter + ('role',)

# Category Admin using DraggableMPTTAdmin remains largely the same.
class CategoryAdmin(DraggableMPTTAdmin):
    form = CategoryAdminForm
    list_display = ('tree_actions', 'indented_title', 'parent', 'created_at')
    list_display_links = ('indented_title',)
    search_fields = ('name',)
    list_filter = ('parent',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('parent')

admin.site.register(Category, CategoryAdmin)

# Tag Admin remains the same.
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

admin.site.register(Tag, TagAdmin)

# Inline for Article Images.
class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 1

# Inline for Comments in Article Admin.
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    fields = ('name', 'email', 'content', 'is_approved')
    readonly_fields = ('created_at',)

# Updated Article Admin to include the author field.
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'is_recommended', 'created_at', 'updated_at')
    list_filter = ('status', 'is_featured', 'is_recommended', 'category')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ArticleImageInline, CommentInline]
    filter_horizontal = ('tags', 'related_articles',)
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'author').prefetch_related('tags', 'related_articles')

admin.site.register(Article, ArticleAdmin)

# Updated Comment Admin to show linked user, if available.
class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'name', 'email', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'email', 'content')
    readonly_fields = ('created_at',)
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"

admin.site.register(Comment, CommentAdmin)
