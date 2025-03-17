from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Category, Tag, Article, ArticleImage, Comment
from .forms import CategoryAdminForm, ArticleAdminForm

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

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

admin.site.register(Tag, TagAdmin)

class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 1

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    fields = ('name', 'email', 'content', 'is_approved')
    readonly_fields = ('created_at',)

class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ('title', 'category', 'status', 'is_featured', 'is_recommended', 'created_at', 'updated_at')
    list_filter = ('status', 'is_featured', 'is_recommended', 'category')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ArticleImageInline, CommentInline]
    filter_horizontal = ('tags', 'related_articles',)
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category').prefetch_related('tags', 'related_articles')

admin.site.register(Article, ArticleAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'name', 'email', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'email', 'content')
    readonly_fields = ('created_at',)
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"

admin.site.register(Comment, CommentAdmin)
