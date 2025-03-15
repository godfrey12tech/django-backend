from django import forms
from .models import Article, Category

class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        parent = cleaned_data.get('parent')

        # Check if the name contains a '>' indicating "Parent > Subcategory"
        if name and '>' in name:
            parts = [part.strip() for part in name.split('>')]
            if len(parts) == 2:
                parent_name, subcat_name = parts
                # If no parent is provided, get or create the parent category
                if not parent:
                    parent_obj, created = Category.objects.get_or_create(
                        name=parent_name,
                        parent=None
                    )
                    cleaned_data['parent'] = parent_obj
                # Set the name to the subcategory name
                cleaned_data['name'] = subcat_name
            else:
                self.add_error('name', "Invalid format. Use 'Parent > Subcategory' format.")
        return cleaned_data

class ArticleAdminForm(forms.ModelForm):
    # Limit the category choices to only subcategories
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(parent__isnull=False),
        required=True,
        help_text="Select a subcategory only. Articles cannot be linked to a parent category."
    )
    
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
