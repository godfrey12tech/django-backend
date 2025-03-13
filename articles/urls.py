from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    CategoryViewSet,
    TagViewSet,
    ArticleViewSet,
    CommentViewSet,
    TopStoriesViewSet,
    RecommendedArticleViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'articles', ArticleViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'top-stories', TopStoriesViewSet, basename='top-stories')
router.register(r'recommended', RecommendedArticleViewSet, basename='recommended')

urlpatterns = [
    path('', include(router.urls)),
]
