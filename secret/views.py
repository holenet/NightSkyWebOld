# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mimetypes
import os
import urllib
from wsgiref.util import FileWrapper

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import dateparse

from secret.forms import TextLogForm, ImageLogForm, PieceForm, PieceCommentForm, WatchForm
from secret.models import Log, Piece, Watch


class HttpSuccess(HttpResponse):
    def __init__(self):
        super(HttpSuccess, self).__init__('Success')


@login_required
def log_list(request, date):
    if date is not None:
        try:
            date = dateparse.parse_date(date)
        except ValueError as ve:
            print(ve)
            raise Http404()
    if date is None:
        logs = Log.objects.filter(author=request.user).order_by('-created_at')
    else:
        logs = Log.objects.filter(author=request.user, datetime__contains=date).order_by('-datetime')
    data = []
    for log in logs:
        item = dict(pk=log.pk, type=log.type, created_at=log.created_at, modified_at=log.modified_at,)
        if log.type == 'text':
            item.update(dict(text=log.text))
        elif log.type == 'image':
            pass
        data.append(item)
    return JsonResponse(data, safe=False)


@login_required
def log_new_text(request):
    if request.method == 'POST':
        form = TextLogForm(request.POST)
        if form.is_valid():
            text_log = form.save(commit=False)
            text_log.author = request.user
            text_log.type = 'text'
            text_log.save()
            return HttpSuccess()
    else:
        form = TextLogForm()
    return render(request, 'secret/standard_edit.html', {'form': form})


@login_required
def log_new_image(request):
    if request.method == 'POST':
        form = ImageLogForm(request.POST, request.FILES)
        if form.is_valid():
            image_log = form.save(commit=False)
            image_log.author = request.user
            image_log.type = 'image'
            image_log.save()
            return HttpSuccess()
    else:
        form = ImageLogForm()
    return render(request, 'secret/file_upload.html', {'form': form})


@login_required
def log_edit_text(request, log_pk):
    log = get_object_or_404(Log, pk=log_pk, type='text', author=request.user)
    if request.method == 'POST':
        form = TextLogForm(request.POST, instance=log)
        if form.is_valid():
            log = form.save(commit=False)
            print(log.pk)
            log.pk = log_pk
            print(log_pk)
            log.notify_modified()
            log.save()
            return HttpSuccess()
    else:
        form = TextLogForm(instance=log)
    return render(request, 'secret/standard_edit.html', {'form': form})


def log_delete_text(request, log_pk):
    log = get_object_or_404(Log, pk=log_pk, type='text', author=request.user)
    if log.watch:
        log.watch.delete()
    log.delete()
    return HttpSuccess()


@login_required
def log_delete_image(request, log_pk):
    log = get_object_or_404(Log, pk=log_pk, type='image', author=request.user)
    path = log.image.path
    try:
        os.remove(path)
    except Exception as e:
        print(e)
    log.delete()
    return HttpSuccess()


@login_required
def log_download_image(request, log_pk):
    log = get_object_or_404(Log, pk=log_pk, type='image', author=request.user)
    image_name = os.path.basename(log.image.name)
    image_path = log.image.path
    wrapper = FileWrapper(file(image_path, 'rb'))
    mimetype = mimetypes.guess_type(image_path)
    response = HttpResponse(wrapper, content_type=mimetype)
    response['X-Sendfile'] = image_path
    response['Content-Length'] = os.stat(image_path).st_size
    response['Content-Disposition'] = 'attachment; filename=%s' % urllib.quote(image_name.encode('utf-8'))
    return response


@login_required
def piece_list(request):
    pieces = Piece.objects.all()
    data = []
    for piece in pieces:
        info = dict(
            pk=piece.pk,
            title=piece.title,
            comment=piece.comment,
            watchs=[dict(start=watch.start, end=watch.end) for watch in piece.watches.all()],
            counts=piece.get_count_watch(),
        )
        started = piece.started_at()
        if started:
            info['started_at'] = started
        ended = piece.ended_at()
        if ended:
            info['ended_at'] = ended
        data.append(info)
    return JsonResponse(data, safe=False)


@login_required
def piece_new(request):
    if request.method == 'POST':
        form = PieceForm(request.POST)
        if form.is_valid():
            piece = form.save(commit=False)
            piece.author = request.user
            piece.save()
            return HttpSuccess()
    else:
        form = PieceForm()
    return render(request, 'secret/standard_edit.html', {'form': form})


@login_required
def piece_edit(request, piece_pk):
    piece = get_object_or_404(Piece, pk=piece_pk, author=request.user)
    if request.method == 'POST':
        form = PieceForm(request.POST, instance=piece)
        if form.is_valid():
            form.save()
            return HttpSuccess()
    else:
        form = PieceForm(instance=piece)
    return render(request, 'secret/standard_edit.html', {'form': form})


@login_required
def piece_comment_edit(request, piece_pk):
    piece = get_object_or_404(Piece, pk=piece_pk, author=request.user)
    if request.method == 'POST':
        form = PieceCommentForm(request.POST, instance=piece)
        if form.is_valid():
            form.save()
            return HttpSuccess()
    else:
        form = PieceCommentForm(instance=piece)
    return render(request, 'secret/standard_edit.html', {'form': form})


@login_required
def piece_delete(request, piece_pk):
    piece = get_object_or_404(Piece, pk=piece_pk, author=request.user)
    piece.delete()
    return HttpSuccess()


@login_required
def watch_list(request):
    watches = Watch.objects.all()
    data = []
    for watch in watches:
        info = dict(
            pk=watch.pk,
            piece=str(watch.piece),
            start=watch.start,
            end=watch.end,
            date=watch.date,
            logs=[dict(pk=log.pk, summary=str(log)) for log in watch.logs.all()],
        )
        data.append(info)
    return JsonResponse(data, safe=False)


@login_required
def watch_new(request):
    if request.method == 'POST':
        form = WatchForm(request.POST)
        if form.is_valid():
            watch = form.save(commit=False)
            watch.author = request.user
            watch.piece = form.cleaned_data['piece']
            watch.save()
            for log in form.cleaned_data['logs']:
                log.watch = watch
                log.save()
            return HttpSuccess()
    else:
        form = WatchForm()
    return render(request, 'secret/standard_edit.html', {'form': form})


@login_required
def watch_edit(request, watch_pk):
    watch = get_object_or_404(Watch, pk=watch_pk, author=request.user)
    if request.method == 'POST':
        form = WatchForm(request.POST, instance=watch)
        if form.is_valid():
            form.save()
    else:
        form = WatchForm(instance=watch)
    return render(request, 'secret/standard_edit.html', {'form': form})


@login_required
def watch_delete(request, watch_pk):
    watch = get_object_or_404(Watch, pk=watch_pk, author=request.user)
    for log in watch.logs:
        log.watch = None
        log.save()
    watch.delete()
    return HttpSuccess()
