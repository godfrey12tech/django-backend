from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404

from .models import Category, Tag, Article, Comment
from .serializers import (
    CategoryTreeSerializer, TagSerializer, ArticleSerializer, CommentSerializer,
    TopStorySerializer, RecommendedArticleSerializer, CategoryMinimalSerializer
)
from .permissions import IsSuperAdmin


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')
    serializer_class = CategoryTreeSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'articles', 'subcategories']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    @method_decorator(cache_page(60 * 15))  # 15-minute cache
    @action(detail=True, methods=['get'])
    def articles(self, request, pk=None):
        category = self.get_object()
        articles = Article.objects.filter(category=category, is_published=True)
        serializer = ArticleSerializer(articles, many=True, context=self.get_serializer_context())
        return Response({"success": True, "data": serializer.data})

    @method_decorator(cache_page(60 * 15))
    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        category = self.get_object()
        subcategories = category.subcategories.all()
        serializer = CategoryMinimalSerializer(subcategories, many=True, context=self.get_serializer_context())
        return Response({"success": True, "data": serializer.data})


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsSuperAdmin]
    http_method_names = ['get', 'post', 'patch', 'delete']


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by('-created_at').select_related('category')
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'category': ['exact'], 'tags': ['exact'], 'status': ['exact'], 'is_published': ['exact'],
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
        context['depth'] = int(self.request.query_params.get('depth', 0))
        return context

    def get_object(self):
        """
        Override get_object to support lookups by both slug and primary key.
        It first tries to find an article with a matching slug, and if not found,
        falls back to a primary key lookup.
        """
        queryset = self.get_queryset()
        lookup_value = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field, None)
        if not lookup_value:
            raise Http404("No lookup value provided.")

        # Try to retrieve by slug first.
        obj = queryset.filter(slug=lookup_value).first()
        if not obj:
            # Fallback to primary key lookup.
            obj = queryset.filter(pk=lookup_value).first()
        if not obj:
            raise Http404("Article not found.")
        self.check_object_permissions(self.request, obj)
        return obj

    @method_decorator(cache_page(60 * 10))  # 10-minute cache
    @action(detail=False, methods=['get'], url_path='slug/(?P<slug>[^/.]+)')
    def retrieve_by_slug(self, request, slug=None):
        if not slug:
            return Response({"success": False, "error": "Slug parameter is required."})
        article = get_object_or_404(Article, slug=slug)
        serializer = self.get_serializer(article)
        return Response({"success": True, "data": serializer.data})

    @method_decorator(cache_page(60 * 10))
    @action(detail=False, methods=['get'], url_path='category-slug/(?P<slug>[^/.]+)')
    def articles_by_category_slug(self, request, slug=None):
        if not slug:
            return Response({"success": False, "error": "Category slug is required."})
        category = get_object_or_404(Category, slug=slug)
        articles = Article.objects.filter(category=category, is_published=True)
        serializer = self.get_serializer(articles, many=True, context=self.get_serializer_context())
        return Response({"success": True, "data": serializer.data})


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at').select_related('article')
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
    permission_classes = [permissions.AllowAny]  # Allow public access

    def get_queryset(self):
        return Article.objects.filter(is_featured=True, status='published').order_by('-created_at')

    @method_decorator(cache_page(60 * 10))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class RecommendedArticleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecommendedArticleSerializer
    permission_classes = [permissions.AllowAny]  # Allow public access

    def get_queryset(self):
        return Article.objects.filter(status='published', is_recommended=True).order_by('-created_at')

    @method_decorator(cache_page(60 * 10))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
