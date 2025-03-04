from rest_framework import serializers
from .models import Category, Tag, Article, Comment, ArticleImage

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'description']

class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    email = serializers.EmailField(write_only=True)  # Hide email on output

    class Meta:
        model = Comment
        fields = [
            'id', 'article', 'name', 'email', 'content',
            'created_at', 'is_approved', 'parent', 'replies'
        ]
        read_only_fields = ['is_approved', 'created_at']

    def get_replies(self, obj):
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data

class ArticleImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ArticleImage
        fields = ['id', 'image_url', 'caption', 'uploaded_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return None

class ArticleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    related_articles = serializers.SerializerMethodField()
    images = ArticleImageSerializer(many=True, read_only=True)  # Removed redundant source argument
    image = serializers.SerializerMethodField()  # Featured image

    # Allow writing category, tags, and related articles via primary keys
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source="category", write_only=True, required=False
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), source="tags", many=True, write_only=True, required=False
    )
    related_articles_ids = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'category', 'category_id',
            'tags', 'tag_ids', 'image', 'images', 'status', 'is_published', 'views', 'likes',
            'reading_time', 'seo_title', 'meta_description', 'is_featured', 'related_articles',
            'related_articles_ids', 'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'views', 'likes']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_related_articles(self, obj):
        related = obj.related_articles.all()[:3]
        return [{'id': art.id, 'title': art.title, 'slug': art.slug} for art in related]

    def create(self, validated_data):
        related_ids = validated_data.pop('related_articles_ids', [])
        article = super().create(validated_data)
        if related_ids:
            article.related_articles.set(related_ids)
        return article

    def update(self, instance, validated_data):
        related_ids = validated_data.pop('related_articles_ids', None)
        article = super().update(instance, validated_data)
        if related_ids is not None:
            article.related_articles.set(related_ids)
        return article
