# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mimetypes
import os
import urllib
from wsgiref.util import FileWrapper

import eyed3
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from cloud.forms import PostForm, CommentForm, UserFileForm, UserFolderForm
from cloud.models import Post, Comment, UserFile, MusicFile


@login_required
def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    if 'JSON' in request.GET:
        data = []
        for post in posts:
            data.append(dict(
                id=post.pk,
                author=str(post.author),
                title=post.title,
                datetime=str(post.published_date),
                text=post.text,
                comment_count=post.comments.count(),
            ))
        return JsonResponse(data, safe=False)
    else:
        return render(request, 'cloud/post_list.html', {'posts': posts})


@login_required
def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if 'JSON' in request.GET:
        data = dict(
            title=post.title,
            author=str(post.author),
        )
        return JsonResponse(data, safe=False)
    else:
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
    post = get_object_or_404(Post, pk=post_id, author=request.user)
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


def get_folder_or_404(path, user=None, user_folder=None):
    arr = path.split(os.path.sep)
    if user_folder is None:
        user_folder = UserFile.objects.filter(author=user, parent=None)
        if len(user_folder) == 0:
            user_folder = UserFile.objects.create(author=user, user_folder='')
        elif len(user_folder) == 1:
            user_folder = user_folder[0]
        else:
            raise Http404()
    if len(arr) == 1 and arr[0] == '':
        return user_folder
    for child in user_folder.children.all():
        if child.name() == arr[0]+os.path.sep:
            return get_folder_or_404(user_folder=child, path=os.path.join(*(arr[1:])))
    raise Http404()


@login_required
def folder_new(request, path):
    parent = get_folder_or_404(user=request.user, path=path)
    if request.method == 'POST':
        form = UserFolderForm(request.POST)
        if form.is_valid():
            user_folder = form.save(commit=False)
            user_folder.author = request.user
            user_folder.parent = parent
            user_folder.save()
            directory = os.path.dirname(os.path.join(settings.MEDIA_ROOT, 'NightSky', user_folder.author.username, user_folder.path()))
            if not os.path.exists(directory):
                os.makedirs(directory)
            return redirect('cloud:file_list', path=parent.path())
    else:
        form = UserFolderForm()
    return render(request, 'cloud/folder_new.html', {'form': form})


@login_required
def folder_delete(request, folder_id, recc=None):
    user_folder = get_object_or_404(UserFile, pk=folder_id, author=request.user)
    for child in user_folder.children.all():
        if child.user_folder is None:
            file_delete(request, child.id, recc=True)
        else:
            folder_delete(request, child.id, recc=True)
    if user_folder.parent is not None:
        path = user_folder.parent.path()
        os.rmdir(os.path.join(settings.MEDIA_ROOT, 'NightSky', user_folder.author.username, user_folder.path()))
        user_folder.delete()
    else:
        path = ''
    if recc is None:
        return redirect('cloud:file_list', path=path)


@login_required
def file_list(request, path):
    parent = get_folder_or_404(user=request.user, path=path)
    user_files = UserFile.objects.filter(author=request.user, parent=parent).order_by('-uploaded_at')\
        .order_by('-user_folder')
    if 'JSON' in request.GET:
        data = []
        for user_file in user_files:
            data.append(dict(
                id=user_file.pk,
                name=os.path.basename(user_file.user_file.name),
                datetime=str(user_file.uploaded_at),
                type=user_file.type,
            ))
        return JsonResponse(data, safe=False)
    else:
        return render(request, 'cloud/file_list.html', {'user_files': user_files, 'parent': parent})


def user_to_music(user_file):
    music_file = MusicFile()
    music_file.pk = user_file.pk
    music_file.author = user_file.author
    music_file.user_file = user_file.user_file
    music_file.parent = user_file.parent
    music_file.type = 'audio'
    return music_file


@login_required
def file_upload(request, path):
    parent = get_folder_or_404(user=request.user, path=path)
    if request.method == 'POST':
        form = UserFileForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('user_file')
            for file in files:
                user_file = UserFile(user_file=file, parent=parent, author=request.user)
                user_file.save()
                if user_file.user_file.name.split('.')[-1] == 'mp3':
                    music_file = user_to_music(user_file)
                    audio_file = eyed3.load(os.path.join(settings.MEDIA_ROOT, music_file.user_file.name))
                    if audio_file is not None:
                        if audio_file.tag.title is not None:
                            music_file.title = audio_file.tag.title
                        if audio_file.tag.artist is not None:
                            music_file.artist = audio_file.tag.artist
                        if audio_file.tag.album is not None:
                            music_file.album = audio_file.tag.album
                        if audio_file.info.time_secs is not None:
                            music_file.length_secs = audio_file.info.time_secs
                    else:
                        music_file.title = music_file.name().split('.')[0]
                    music_file.save()
                else:
                    user_file.save()
            return redirect('cloud:file_list', path=parent.path())
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
def file_delete(request, file_id, recc=None):
    user_file = get_object_or_404(UserFile, pk=file_id, author=request.user)
    path = user_file.parent.path()
    os.remove(os.path.join(settings.MEDIA_ROOT, user_file.user_file.name))
    user_file.delete()
    if recc is None:
        return redirect('cloud:file_list', path=path)


@login_required
def music_list(request):
    musics = MusicFile.objects.filter(author=request.user).order_by('-uploaded_at')
    if 'JSON' in request.GET:
        data = []
        for music in musics:
            data.append(dict(
                id=music.pk,
                title=music.title,
                artist=music.artist,
                album=music.album,
                path=music.user_file.name,
            ))
        return JsonResponse(data, safe=False)
    else:
        return HttpResponseNotFound()


@login_required
def music_detail(request, file_id):
    music = get_object_or_404(MusicFile, pk=file_id, author=request.user)
    if 'JSON' in request.GET:
        data = dict(
            title=music.title,
            artist=music.artist,
            album=music.album,
            path=music.user_file.name,
        )
        return JsonResponse(data, safe=False)
    else:
        return HttpResponseNotFound()


@login_required
def post_find_by_index(request, post_index):
    post = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')[int(post_index)]
    queries = dict(
        title=post.title,
        text=post.text,
        author=str(post.author),
        datetime=str(post.published_date),
        id=post.pk,
        comment_count=post.comments.count(),
    )
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


@login_required
def post_recent(request):
    post = Post.objects.all().order_by('-published_date')[0]
    if post is None:
        return HttpResponseNotFound()
    data = dict(id=post.pk, author=str(post.author))
    return JsonResponse(data, safe=False)
