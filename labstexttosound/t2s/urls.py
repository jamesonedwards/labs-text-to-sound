from django.conf.urls.defaults import patterns, url
from django.conf import settings

urlpatterns = patterns('t2s.views',
    url(r'^texttosound/$', 'texttosound', name='texttosound'),
    url(r'^labstexttosound/texttosound/$', 'texttosound', name='texttosound'),
    url(r'^playtwitterfeed/$', 'playtwitterfeed', name='playtwitterfeed'),
    url(r'^labstexttosound/playtwitterfeed/$', 'playtwitterfeed', name='playtwitterfeed'),
    url(r'^testpost/$', 'testpost', name='testpost'),
    url(r'^labstexttosound/testpost/$', 'testpost', name='testpost'),
    url(r'^playlabsmb/$', 'playlabsmb', name='playlabsmb'),
    url(r'^labstexttosound/playlabsmb/$', 'playlabsmb', name='playlabsmb')
)

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}))
else:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}))