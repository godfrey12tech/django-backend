from django import forms
from .models import Article

class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 20,  # Increase the number of rows
                'cols': 100,
                'style': 'width: 100%; resize: vertical;'  # Allow vertical resizing
            }),
        }
