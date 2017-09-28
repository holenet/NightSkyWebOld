# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mimetypes
import os
import urllib
from wsgiref.util import FileWrapper

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from cloud.forms import PostForm, CommentForm, UserFileForm
from cloud.models import Post, Comment, UserFile


@login_required
def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    return render(request, 'cloud/post_list.html', {'posts': posts})


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'cloud/post_detail.html', {'post': post})


@login_required
def post_new(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('cloud:post_detail', post_id=post.pk)
    else:
        form = PostForm()
    return render(request, 'cloud/post_edit.html', {'form': form, 'mode': 'New Post'})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('cloud:post_detail', post_id=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'cloud/post_edit.html', {'form': form, 'mode': 'Edit Post'})


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.delete()
    return redirect('cloud:post_list')


@login_required
def add_comment_to_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('cloud:post_detail', post_id=post.pk)
    else:
        form = CommentForm()
    return render(request, 'cloud/add_comment_to_post.html', {'form': form})


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.delete()
    return redirect('cloud:post_detail', post_id=comment.post.pk)


@login_required
def file_list(request):
    user_files = UserFile.objects.filter(author=request.user).order_by('-uploaded_at')
    return render(request, 'cloud/file_list.html', {'user_files': user_files})


@login_required
def file_upload(request):
    if request.method == 'POST':
        form = UserFileForm(request.POST, request.FILES)
        if form.is_valid():
            user_file = form.save(commit=False)
            user_file.author = request.user
            if user_file.description == '':
                user_file.description = os.path.basename(user_file.user_file.name)
            user_file.save()
            return redirect('cloud:file_list')
    else:
        form = UserFileForm()
    return render(request, 'cloud/file_upload.html', {'form': form})


@login_required
def file_download(request, file_id):
    user_file = get_object_or_404(UserFile, pk=file_id, author=request.user)
    file_name = os.path.basename(user_file.user_file.name)
    file_path = os.path.join(settings.MEDIA_ROOT, user_file.user_file.name)
    file_wrapper = FileWrapper(file(file_path, 'rb'))
    file_mimetype = mimetypes.guess_type(file_path)
    response = HttpResponse(file_wrapper, content_type=file_mimetype)
    response['X-Sendfile'] = file_path
    response['Content-Length'] = os.stat(file_path).st_size
    response['Content-Disposition'] = 'attachment; filename=%s' % urllib.quote(file_name.encode('utf-8'))
    return response


@login_required
def post_find_by_index(request, post_index):
    post = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')[int(post_index)]
    queries = dict(
        title=post.title,
        text=post.text,
        author=str(post.author),
        datetime=str(post.published_date),
        id=post.pk)
    comments = post.comments.all()
    comments_list = []
    for comment in comments:
        comment_dict = dict(
            author=str(comment.author),
            text=comment.text,
            datetime=str(comment.created_date),
            id=comment.pk)
        comments_list.append(comment_dict)
    queries['comments'] = comments_list
    return JsonResponse(queries, safe=False)
