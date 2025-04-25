import os
from glob import glob
from django.core.management.base import BaseCommand
from articles.services.doc_importer import ArticleImporter

class Command(BaseCommand):
    help = "Import .docx files from import_docs/ as Articles (title, slug, excerpt, content, images)"

    IMPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'import_docs'))

    def handle(self, *args, **options):
        os.makedirs(self.IMPORT_DIR, exist_ok=True)
        pattern = os.path.join(self.IMPORT_DIR, '*.docx')
        for filepath in glob(pattern):
            self.stdout.write(f"Importing {filepath}...")
            try:
                importer = ArticleImporter(docx_path=filepath)
                article = importer.import_article()
                self.stdout.write(self.style.SUCCESS(f"✅ Created Article #{article.pk}: {article.title}"))
                os.rename(filepath, filepath + '.imported')
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Failed to import {filepath}: {e}"))
