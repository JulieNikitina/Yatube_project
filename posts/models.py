from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    slug = models.SlugField(blank=False, unique=True)
    title = models.CharField(
        'название',
        blank=False,
        max_length=200,
        unique=True
    )
    description = models.TextField('описание')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('текст', help_text='Введите текст вашего поста')
    pub_date = models.DateTimeField('дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        help_text='необязательно',
        null=True,
        related_name='posts',
        verbose_name='группа',
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True, null=True,
        verbose_name='Изображение',
        help_text='Загрузите изображение',
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        name_author = self.author
        cut_text = self.text[0:10]
        return f'{name_author}: {cut_text}'


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField('текст', help_text='Напишите ваш комментарий')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        date = self.created
        author = self.author
        cut_text = self.text[0:10]
        return f'{author}.{date}.{cut_text}'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        unique_together = ['user', 'author']
