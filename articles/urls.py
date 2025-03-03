from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import CategoryViewSet, TagViewSet, ArticleViewSet, CommentViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'articles', ArticleViewSet)
router.register(r'comments', CommentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
