from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Tag, Article, Comment
from .serializers import CategorySerializer, TagSerializer, ArticleSerializer, CommentSerializer
from .permissions import IsSuperAdmin  # Custom permission for admin-only modifications

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsSuperAdmin]

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def articles(self, request, pk=None):
        """Retrieve all articles under a specific category."""
        category = self.get_object()
        articles = Article.objects.filter(category=category, is_published=True).order_by('-created_at')
        serializer = ArticleSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsSuperAdmin]

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all().order_by('-created_at')
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'tags', 'status', 'is_published']
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['created_at', 'updated_at']

    def get_permissions(self):
        """
        Public users can view articles (list, retrieve),
        but only superadmins can create, update, or delete.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get_serializer_context(self):
        """Pass request in serializer context for building absolute URLs."""
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['article']
    search_fields = ['name', 'content']

    def get_permissions(self):
        """
        Public users can view and create comments,
        but only superadmins can update or delete them.
        """
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]
