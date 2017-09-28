from django import forms
from .models import Post, Comment, UserFile


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text',)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class UserFileForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = UserFile
        fields = ('user_file', 'description',)
