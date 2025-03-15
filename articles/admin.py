from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Category, Tag, Article, ArticleImage, Comment
from .forms import CategoryAdminForm, ArticleAdminForm

# Custom CategoryAdmin using DraggableMPTTAdmin with our CategoryAdminForm.
# This will display the category tree and allow you to enter categories using "Parent > Subcategory" syntax.
class CategoryAdmin(DraggableMPTTAdmin):
    form = CategoryAdminForm
    list_display = ('tree_actions', 'indented_title', 'parent')
    list_display_links = ('indented_title',)

admin.site.register(Category, CategoryAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Tag, TagAdmin)

class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 1

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1

# ArticleAdmin uses the custom ArticleAdminForm so that only subcategories are available in the category field.
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ('title', 'category', 'status', 'is_featured', 'is_recommended', 'created_at', 'updated_at')
    list_filter = ('status', 'is_featured', 'is_recommended', 'category')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ArticleImageInline, CommentInline]
    filter_horizontal = ('tags', 'related_articles',)

admin.site.register(Article, ArticleAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'name', 'email', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'email', 'content')

admin.site.register(Comment, CommentAdmin)
