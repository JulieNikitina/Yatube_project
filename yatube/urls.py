from django.conf import settings
from django.conf.urls import handler404, handler500
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.flatpages import views
from django.urls import include, path

handler404 = "posts.views.page_not_found"  # noqa
handler500 = "posts.views.server_error"  # noqa


# По замечанию про перекрытие путей: как я понимаю, что проблема состоит в том,
# что если пользователь будет иметь имя admin, то он не сможет попасть на свой
# профиль. И решить это можно либо запретом на имя admin при создании профиля
# либо изменением posts/urls пути '<str:username>/' на что-нибудь вроде
# users/<str:username>
# если мне не изменяем память, пути эти я прописывала по заданиям из теории,
# лучше исправить?

urlpatterns = [
    path('about/', include('django.contrib.flatpages.urls')),
    path(
        'about-author/',
        views.flatpage,
        {'url': '/about-author/'},
        name='author'
    ),
    path('about-spec/', views.flatpage, {'url': '/about-spec/'}, name='spec'),
    path('about-us/', views.flatpage, {'url': '/about-us/'}, name='about'),
    path('terms/', views.flatpage, {'url': '/terms/'}, name='terms'),
    path('contacts/', views.flatpage, {'url': '/contacts/'}, name='contacts'),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include('posts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
