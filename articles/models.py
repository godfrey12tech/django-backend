from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from mptt.models import MPTTModel, TreeForeignKey

class Category(MPTTModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    parent = TreeForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    # These MPTT fields are maintained automatically by django-mptt.
    lft = models.PositiveIntegerField(default=0, editable=False)
    rght = models.PositiveIntegerField(default=0, editable=False)
    tree_id = models.PositiveIntegerField(default=0, editable=False)
    level = models.PositiveIntegerField(default=0, editable=False)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        ordering = ['tree_id', 'lft']

    def __str__(self):
        # For a two-level system, we can display subcategories as "Parent > Subcategory"
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name or "Unnamed Category"

    def clean(self):
        """
        Enforce that if a category has a parent, that parent must be a top-level category.
        This means we only allow two levels: a parent and its subcategories.
        """
        super().clean()
        if self.parent and self.parent.parent:
            raise ValidationError("Subcategories can only have a top-level parent (only one level of nesting is allowed).")

class Tag(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name or "Unnamed Tag"

class Article(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_published = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    reading_time = models.IntegerField(default=0)
    seo_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)      # For marking as top stories
    is_recommended = models.BooleanField(default=False)     # For recommended articles
    related_articles = models.ManyToManyField("self", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
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
