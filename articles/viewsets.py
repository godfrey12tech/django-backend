from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Tag, Article, Comment
from .serializers import (
    CategoryTreeSerializer,
    TagSerializer,
    ArticleSerializer,
    CommentSerializer,
    TopStorySerializer,
    RecommendedArticleSerializer,
    CategoryMinimalSerializer
)
from .permissions import IsSuperAdmin

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category.
    Lists only top-level categories and provides custom actions for articles and subcategories.
    """
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
    serializer_class = CategoryTreeSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'articles', 'subcategories']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def articles(self, request, pk=None):
        """
        Return published articles for the given category.
        """
        category = self.get_object()
        articles = Article.objects.filter(
            category=category, 
            is_published=True
        ).order_by('-created_at').select_related('category')
        
        serializer = ArticleSerializer(
            articles, 
            many=True,
            context=self.get_serializer_context()
        )
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """
        Return a list of direct subcategories using the minimal serializer.
        """
        category = self.get_object()
        subcategories = category.subcategories.all()
        serializer = CategoryMinimalSerializer(
            subcategories, 
            many=True,
            context=self.get_serializer_context()
        )
        return Response({"success": True, "data": serializer.data})


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsSuperAdmin]
    http_method_names = ['get', 'post', 'patch', 'delete']


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by('-created_at').select_related('category').prefetch_related('tags', 'related_articles')
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category': ['exact'],
        'tags': ['exact'],
        'status': ['exact'],
        'is_published': ['exact'],
        'created_at': ['gte', 'lte']
    }
    search_fields = ['title', 'content', 'excerpt', 'seo_title']
    ordering_fields = ['created_at', 'updated_at', 'views', 'likes']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'retrieve_by_slug', 'articles_by_category_slug']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            context['depth'] = int(self.request.query_params.get('depth', 0))
        except Exception as e:
            context['depth'] = 0
        return context

    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def retrieve_by_slug(self, request, slug=None):
        """
        Retrieve an article based on its slug.
        SEO-friendly endpoint: /api/articles/slug/<article-slug>/
        """
        if not slug:
            return Response(
                {"success": False, "error": "Slug parameter is required"}, 
                status=400
            )
        article = get_object_or_404(Article, slug=slug)
        serializer = self.get_serializer(article)
        return Response({"success": True, "data": serializer.data})

    @action(detail=False, methods=['get'], url_path='category-slug/(?P<slug>[^/.]+)')
    def articles_by_category_slug(self, request, slug=None):
        """
        Retrieve articles for a category based on the category slug.
        SEO-friendly endpoint: /api/articles/category-slug/<category-slug>/?page=1&limit=10
        """
        if not slug:
            return Response(
                {"success": False, "error": "Category slug is required"},
                status=400
            )
        from .models import Category  # ensure Category is imported
        category = get_object_or_404(Category, slug=slug)
        articles = Article.objects.filter(
            category=category, 
            is_published=True
        ).order_by('-created_at').select_related('category')
        serializer = self.get_serializer(articles, many=True, context=self.get_serializer_context())
        return Response({"success": True, "data": serializer.data})


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at').select_related('article', 'parent')
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['article', 'is_approved']
    search_fields = ['name', 'content']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class TopStoriesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TopStorySerializer

    def get_queryset(self):
        return Article.objects.filter(
            is_featured=True,
            status='published'
        ).order_by('-views')[:10]


class RecommendedArticleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecommendedArticleSerializer
    
    def get_queryset(self):
        return Article.objects.filter(
            status='published',
            is_recommended=True
        ).order_by('-created_at')[:10]
