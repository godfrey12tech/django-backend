from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import AbstractUser


# Custom User Model
class User(AbstractUser):
    dummy_field = models.CharField(max_length=1, default='a')

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('user', 'User'),
    ]
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        help_text="Designates the type of user."
    )

    def __str__(self):
        return self.username


class Category(MPTTModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    # MPTT-managed fields:
    lft = models.PositiveIntegerField(default=0, editable=False)
    rght = models.PositiveIntegerField(default=0, editable=False)
    tree_id = models.PositiveIntegerField(default=0, editable=False)
    level = models.PositiveIntegerField(default=0, editable=False)
    
    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    class Meta:
        ordering = ['tree_id', 'lft']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name or "Unnamed Category"
    
    def clean(self):
        super().clean()
        # Enforce that if a category has a parent, that parent must be top-level.
        # This ensures only two levels: a parent and its subcategories.
        if self.parent and self.parent.parent:
            raise ValidationError("Subcategories can only have a top-level parent (only one level of nesting is allowed).")
    
    def generate_unique_slug(self, slug_base):
        """Generate a unique slug by appending a number or random string if needed."""
        slug = slug_base
        num = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{num}"
            num += 1
        return slug
    
    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided.
        if not self.slug and self.name:
            slug_base = slugify(self.name)
            self.slug = self.generate_unique_slug(slug_base)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    # Timestamp fields for Tag
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name or "Unnamed Tag"


class Article(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    title = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, default='default-slug')
    content = models.TextField(blank=True, null=True)
    excerpt = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles"
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="articles"
    )
    image = models.ImageField(
        upload_to='article_images/',
        blank=True,
        null=True
    )
    # Link each article to an author (custom user)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="author_articles"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_published = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    reading_time = models.IntegerField(default=0)
    seo_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_recommended = models.BooleanField(default=False)
    related_articles = models.ManyToManyField("self", symmetrical=False, blank=True, related_name="related_to")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def clean(self):
        super().clean()
        # Enforce that if an article is linked to a category,
        # that category must be a subcategory (i.e. it must have a parent).
        if self.category and self.category.parent is None:
            raise ValidationError("Articles must be linked to a subcategory, not a parent category.")
    
    def generate_unique_slug(self, slug_base):
        """Generate a unique slug by appending a number or random string if needed."""
        slug = slug_base
        num = 1
        while Article.objects.filter(slug=slug).exists():
            slug = f"{slug_base}-{num}"
            num += 1
        return slug

    def save(self, *args, **kwargs):
        # Validate before saving.
        self.full_clean()
        if not self.slug and self.title:
            slug_base = slugify(self.title)
            self.slug = self.generate_unique_slug(slug_base)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title or "Untitled Article"


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='article_images/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.article.title or 'Untitled'}"


class Comment(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    # Optional: Link comment to a user if logged in
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comments'
    )
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="replies"
    )
    
    def __str__(self):
        return f"Comment on {self.article.title or 'Untitled'}"
