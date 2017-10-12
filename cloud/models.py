# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.utils import timezone

from django.db import models


class Post(models.Model):
    author = models.ForeignKey('auth.User')
    title = models.CharField(max_length=200)
    text = models.TextField()
    published_date = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u'%s' % self.title


class Comment(models.Model):
    post = models.ForeignKey('cloud.Post', related_name='comments')
    author = models.ForeignKey('auth.User')
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u'%s' % self.text


def user_file_path(instance, filename):
    return os.path.join('NightSky', instance.author.username, instance.path())


class UserFile(models.Model):
    parent = models.ForeignKey('cloud.UserFile', related_name='children', null=True)
    author = models.ForeignKey('auth.User')
    user_file = models.FileField(upload_to=user_file_path, null=True)
    user_folder = models.TextField(null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    type = models.CharField(max_length=20, default='etc')

    def name(self):
        if self.user_folder is not None:
            return self.user_folder+os.path.sep
        return os.path.basename(self.user_file.name)

    def path(self):
        if self.parent is None:
            return ''
        return self.parent.path()+self.name()

    def path_recurr(self, arr):
        if self.parent is None:
            return arr
        for i in range(len(arr)):
            arr[i] = ' '+arr[i]
        arr.insert(0, self.name())
        print('\n'.join(arr))
        print()
        return self.parent.path_recurr(arr)

    def path_stair(self):
        return '\n'.join(self.path_recurr([]))

    def __unicode__(self):
        return u'%s' % (self.path())


class MusicFile(UserFile):
    title = models.TextField(default='')
    artist = models.TextField(default='')
    album = models.TextField(default='')
    length_secs = models.IntegerField(default=-1)

    def __unicode__(self):
        return u'%s-%s' % (self.title, self.artist)
