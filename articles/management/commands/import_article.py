import frontmatter
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from articles.models import Article, Category, Tag

class Command(BaseCommand):
    help = 'Imports an article from a Markdown file into the SQLite dev database'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help='Path to the Markdown file.')

    def handle(self, *args, **kwargs):
        filepath = kwargs['filepath']
        
        # Load and parse the Markdown file using python-frontmatter
        post = frontmatter.load(filepath)
        
        # Extract fields from the YAML front matter
        title = post.get("title")
        slug_val = post.get("slug")
        description = post.get("description")
        content = post.content  # Markdown content
        excerpt = post.get("excerpt", content[:150])
        seo_title = post.get("seo_title")
        meta_description = post.get("meta_description")
        
        # Process Category and Parent Category using slug for lookup
        parent_category_name = post.get("parent_category")
        category_name = post.get("category")
        
        if parent_category_name:
            # Lookup or create the parent category using its slug
            parent_slug = slugify(parent_category_name)
            parent_category, _ = Category.objects.get_or_create(
                slug=parent_slug,
                defaults={'name': parent_category_name}
            )
            # Lookup or create the subcategory with the parent set
            category_slug = slugify(category_name)
            category, created = Category.objects.get_or_create(
                slug=category_slug,
                defaults={'name': category_name, 'parent': parent_category}
            )
            # If the category exists but doesn't have a parent, update it.
            if not created and category.parent is None:
                category.parent = parent_category
                category.save()
        else:
            # If no parent_category is provided, lookup or create the category by slug
            category_slug = slugify(category_name)
            category, _ = Category.objects.get_or_create(
                slug=category_slug,
                defaults={'name': category_name}
            )
        
        # Create the Article instance with the mapped fields.
        article = Article.objects.create(
            title=title,
            slug=slug_val,
            content=content,
            excerpt=excerpt,
            category=category,
            seo_title=seo_title,
            meta_description=meta_description,
            status='published',   # Adjust if necessary
            is_published=True,
        )
        
        # Process Tags (ManyToMany field)
        tags = post.get("tags", [])
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'description': ''}
            )
            article.tags.add(tag)
        
        article.save()
        self.stdout.write(self.style.SUCCESS(f"Article '{title}' imported successfully."))
