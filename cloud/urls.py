from django.conf.urls import url
from . import views

app_name = 'cloud'
urlpatterns = [
    # post
    url(r'^$', views.post_list, name='post_list'),
    url(r'^post/(?P<post_id>[0-9]+)/$', views.post_detail, name='post_detail'),
    url(r'^post/new/$', views.post_new, name='post_new'),
    url(r'^post/(?P<post_id>[0-9]+)/edit/$', views.post_edit, name='post_edit'),
    url(r'^post/(?P<post_id>[0-9]+)/delete/$', views.post_delete, name='post_delete'),
    url(r'^post/(?P<post_id>[0-9]+)/comment/$', views.add_comment_to_post, name='add_comment_to_post'),
    url(r'^comment/(?P<comment_id>[0-9]+)/delete/$', views.comment_delete, name='comment_delete'),

    # file
    url(r'^file/$', views.file_list, name='file_list'),
    url(r'^file/upload/$', views.file_upload, name='file_upload'),
    url(r'^file/download/(?P<file_id>[0-9]+)/$', views.file_download, name='file_download'),

    # json-only
    url(r'^post/find-by-index/(?P<post_index>[0-9]+)/$', views.post_find_by_index, name='post_find_by_index'),
    url(r'^post/recent/$', views.post_recent, name='post_recent'),
]
