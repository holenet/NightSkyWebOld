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
    user_file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = UserFile
        fields = ('user_file',)


class UserFolderForm(forms.ModelForm):
    class Meta:
        model = UserFile
        fields = ('user_folder',)
