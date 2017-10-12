# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.db import models
from django.utils import timezone


def image_path(instance, filename):
    return os.path.join('image', instance.author.username, filename)


class Log(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(null=True)
    author = models.ForeignKey('auth.User')
    type = models.TextField()
    text = models.TextField(null=True)
    image = models.ImageField(null=True)
    watch = models.ForeignKey('secret.Watch', related_name='logs', on_delete=models.SET_NULL, null=True)

    def __unicode__(self):
        return u'%d [%s] -%s' % (self.id, self.type, self.created_at)

    def notify_modified(self):
        self.modified_at = timezone.now()


class Piece(models.Model):
    author = models.ForeignKey('auth.User')
    title = models.TextField()
    comment = models.TextField(default='')

    def __unicode__(self):
        return u'%s' % self.title

    def started_at(self):
        if self.watches.count()>0:
            return self.watches.order_by('date')[0].date
        return None

    def ended_at(self):
        if self.watches.count()>0:
            return self.watches.order_by('-date')[0].date
        return None

    def get_count_watch(self):
        count = []
        for watch in self.watches.order_by('-end'):
            s = watch.start
            e = watch.end
            if len(count)<e:
                count += [0]*(e-len(count))
            for i in range(s, e+1):
                count[i-1] += 1
        return count


class Watch(models.Model):
    author = models.ForeignKey('auth.User')
    piece = models.ForeignKey('secret.Piece', related_name='watches', on_delete=models.SET_NULL, null=True)
    start = models.PositiveSmallIntegerField()
    end = models.PositiveSmallIntegerField()
    date = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u'%s [%d-%d]' % (self.piece, self.start, self.end)
