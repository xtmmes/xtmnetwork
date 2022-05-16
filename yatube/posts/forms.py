from django import forms
from django.contrib.auth import get_user_model

from .models import Comment, Post


User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

        labels = {
            'text': 'Текст',
            'group': 'Группа'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
