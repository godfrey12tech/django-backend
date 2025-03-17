from rest_framework import serializers
from django.utils.text import slugify
from .models import Category, Tag, Article, Comment, ArticleImage

# ================== Category Serializers ==================
class CategoryMinimalSerializer(serializers.ModelSerializer):
    """Minimal representation of a Category for nested usage with slug fallback."""
    slug = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

    def get_slug(self, obj):
        # Return the slug if set; otherwise, generate one from the name.
        return obj.slug if obj.slug else slugify(obj.name or "")


class CategoryTreeSerializer(serializers.ModelSerializer):
    """
    Serializer for Category detail endpoints.
    Includes direct subcategories (limited to one level to avoid infinite recursion).
    """
    slug = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'subcategories']

    def get_slug(self, obj):
        return obj.slug if obj.slug else slugify(obj.name or "")

    def get_subcategories(self, obj):
        # Use the context depth to limit recursion: only one level of subcategories is included.
        current_depth = self.context.get('depth', 0)
        if int(current_depth) >= 1:
            return []
        return CategoryMinimalSerializer(
            obj.subcategories.all(),
            many=True,
            context={'depth': int(current_depth) + 1}
        ).data

# ================== Tag Serializer ==================
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'description']

# ================== Comment Serializer ==================
class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'article', 'name', 'email', 'content', 'created_at', 
                  'is_approved', 'parent', 'replies']
        read_only_fields = ['is_approved', 'created_at']

    def get_replies(self, obj):
        # Return a limited number of replies to avoid deep recursion.
        return CommentSerializer(
            obj.replies.all(),
            many=True,
            context=self.context
        ).data[:5]

# ================== Article Image Serializer ==================
class ArticleImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ArticleImage
        fields = ['id', 'image_url', 'caption', 'uploaded_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image else None

# ================== Article Serializer ==================
class ArticleSerializer(serializers.ModelSerializer):
    # Use minimal representations for nested relations to avoid recursion.
    category = CategoryMinimalSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    related_articles = serializers.SerializerMethodField()
    images = ArticleImageSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    # Writeable fields for associations.
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        source="category", 
        write_only=True, 
        required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        source="tags",
        many=True,
        write_only=True,
        required=False
    )
    related_articles_ids = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'category', 'category_id',
            'tags', 'tag_ids', 'image', 'images', 'status', 'is_published', 'views', 
            'likes', 'reading_time', 'seo_title', 'meta_description', 'is_featured', 
            'related_articles', 'related_articles_ids', 'comments', 'created_at', 
            'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'views', 'likes']

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    def get_related_articles(self, obj):
        # Return up to three related articles in minimal representation.
        return [{
            'id': art.id,
            'title': art.title,
            'slug': art.slug
        } for art in obj.related_articles.all()[:3]]

    def create(self, validated_data):
        related_ids = validated_data.pop('related_articles_ids', [])
        article = super().create(validated_data)
        article.related_articles.set(related_ids)
        return article

    def update(self, instance, validated_data):
        related_ids = validated_data.pop('related_articles_ids', None)
        article = super().update(instance, validated_data)
        if related_ids is not None:
            article.related_articles.set(related_ids)
        return article

# ================== Specialized Serializers ==================
class TopStorySerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['id', 'excerpt', 'link']

    def get_link(self, obj):
        # Use category slug if available; fallback to generating one from the name.
        base_slug = obj.category.slug if obj.category and obj.category.slug else (
            slugify(obj.category.name) if obj.category and obj.category.name else "uncategorized"
        )
        return f"/category/{base_slug}/{obj.slug}/"

    def get_excerpt(self, obj):
        # Return the excerpt if available; otherwise, use the first 150 characters of the content.
        return obj.excerpt if obj.excerpt else (obj.content[:150] if obj.content else "")


class RecommendedArticleSerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['id', 'title', 'link']

    def get_link(self, obj):
        base_slug = obj.category.slug if obj.category and obj.category.slug else (
            slugify(obj.category.name) if obj.category and obj.category.name else "uncategorized"
        )
        return f"/category/{base_slug}/{obj.slug}/"
