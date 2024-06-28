from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ('author', 'created_at', 'is_published')
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }
