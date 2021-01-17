import os

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User


class PostPageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.client_logout = Client()
        self.client_second = Client()
        self.user = User.objects.create_user(username='user', password='12345')
        self.author = User.objects.create_user(
            username='author',
            password='12345'
        )
        self.user_second = User.objects.create_user(
            username='user_second',
            password='12345'
        )
        self.client.force_login(self.user)
        self.client_second.force_login(self.user_second)
        self.group_first = Group.objects.create(
            description='test_group_description',
            slug='test_group_slug',
            title='test_group_title'
        )
        self.group_second = Group.objects.create(
            description='second_test_group_description',
            slug='second_test_group_slug',
            title='second_test_group_title'
        )
        cache.clear()

    def post_is_real(self, response, test_post):
        paginator = response.context.get('paginator')
        if paginator is not None:
            self.assertEqual(paginator.count, 1)
            post = response.context['page'][0]
        else:
            post = response.context['post']
        self.assertEqual(post.text, test_post.text)
        self.assertEqual(post.author, test_post.author)
        self.assertEqual(post.group, test_post.group)
        self.assertEqual(post.pub_date, test_post.pub_date)

    def urls_list(self, post):
        urls_list = [
            reverse('index'),
            reverse('profile', args=[post.author]),
            reverse('post', args=[post.author, post.id]),
            reverse('group_posts', args=[post.group.slug])
        ]
        return urls_list

    def test_user_page(self):
        response = self.client.get(
            reverse('profile', args=[self.user.username])
        )
        self.assertEqual(response.status_code, 200)

    def test_new_post_login(self):
        response = self.client.post(
            reverse('new_post'),
            {'group': self.group_first.id, 'text': 'First test text'},
            follow=True
        )
        test_post = Post.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(test_post.text, 'First test text')
        self.assertEqual(test_post.group.id, self.group_first.id)
        self.assertEqual(test_post.author.username, self.user.username)

    def test_post_in_pages(self):
        test_text = 'Second test-text'
        self.assertEqual(Post.objects.count(), 0)
        test_post = Post.objects.create(
            text=test_text,
            author=self.user,
            group=self.group_first
        )
        for url in self.urls_list(test_post):
            with self.subTest(url=url):
                response_url = self.client.get(url)
                self.post_is_real(response_url, test_post)

    def test_post_edit(self):
        test_post_for_edit = Post.objects.create(
            text='Test text for edit',
            author=self.user,
            group=self.group_first
        )
        edit_text = 'New text for edit test'
        self.client.post(
            reverse('post_edit', args=[self.user, test_post_for_edit.id]),
            {'text': edit_text, 'group': self.group_second.id}
        )
        post = Post.objects.get(id=test_post_for_edit.id)
        for url in self.urls_list(post):
            with self.subTest(url=url):
                response_url = self.client.get(url)
                self.post_is_real(response_url, post)

    def test_new_post_logout(self):
        login_url = reverse('login')
        new_post_url = reverse('new_post')
        target_url = f'{login_url}?next={new_post_url}'
        response = self.client_logout.get(reverse('new_post'), follow=True)
        self.assertRedirects(response, target_url)
        count = Post.objects.count()
        self.assertEqual(count, 0)

    def test_404(self):
        response = self.client.get('/test_path/')
        self.assertEqual(response.status_code, 404)

    def test_image(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile(
            name='image.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post = Post.objects.create(
            author=self.user,
            text='text',
            group=self.group_first,
            image=img)
        for url in self.urls_list(post):
            with self.subTest(url=url):
                response_url = self.client.get(url)
                self.assertContains(response_url, '<img')
        os.remove('media/posts/image.gif')

    def test_not_image(self):
        not_image = SimpleUploadedFile(
            name='text.txt',
            content=b'abc',
            content_type='text/plain'
        )
        response = self.client.post(
            reverse('new_post'),
            {
                'text': 'Text for post with image',
                'group': self.group_first.id,
                'image': not_image
            },
            follow=True
        )
        self.assertFormError(
            response,
            'form',
            'image',
            errors=[
                'Загрузите правильное изображение. '
                'Файл, который вы загрузили, поврежден или не является '
                'изображением.'
            ]
        )

    def test_cache(self):
        # запрос к странице до создания поста
        response_empty = self.client.get(reverse('index'))
        # создали пост
        test_post = Post.objects.create(
            text="Cache_Test_text",
            author=self.user,
            group=self.group_first
        )
        # проверили что он есть на странице
        response = self.client.get(reverse('index'))
        post = response.context['page'][0]
        self.assertEqual(post.text, test_post.text)
        self.assertEqual(post.author, test_post.author)
        self.assertEqual(post.group, test_post.group)
        self.assertEqual(post.pub_date, test_post.pub_date)
        # удалили пост
        Post.objects.filter(id=post.id).delete()
        # проверили что он удалился  в БД
        self.assertEqual(Post.objects.count(), 0)
        response_second = self.client.get(reverse('index'))
        # проверили что на странице он еще есть
        self.assertEqual(response.content, response_second.content)
        cache.clear()
        response_third = self.client.get(reverse('index'))
        # проверили идентичность контента до создания поста и после
        self.assertEqual(response_empty.content, response_third.content)

    def test_following(self):
        self.client_logout.post('profile_follow', args=[self.author.username])
        self.assertEqual(Follow.objects.count(), 0)
        response = self.client.post(
            reverse('profile_follow', args=[self.author.username]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Follow.objects.count(), 1)
        follow = Follow.objects.first()
        self.assertEqual(follow.author, self.author)
        self.assertEqual(follow.user, self.user)

    def test_unfollowing(self):
        Follow.objects.create(user=self.user, author=self.author)
        self.assertEqual(Follow.objects.count(), 1)
        response = self.client.post(
            reverse(
                'profile_unfollow',
                args=[self.author.username]
            ),
            follow=True
        )
        self.assertEqual(Follow.objects.count(), 0)
        self.assertEqual(response.status_code, 200)

    def test_index_follow_login_user(self):
        Follow.objects.create(user=self.user, author=self.author)
        test_post = Post.objects.create(
            text='test_text',
            author=self.author,
            group=self.group_first
        )
        response = self.client.get(reverse('follow_index'))
        # но в ТЗ у нас нужно проверить что "пост появляется в ленте", не
        # значит ли это, что проверяем как раз шаблон?
        self.post_is_real(response, test_post)
        # варианта изящнее, как через контекст проверить отсутствие поста,
        # не придумалось
        response_second = self.client_second.get(reverse('follow_index'))
        count = len(response_second.context['page'])
        self.assertEqual(count, 0)

    def test_index_follow_logout_user(self):
        login_url = reverse('login')
        follow_url = reverse('follow_index')
        response = self.client_logout.get(follow_url)
        target_url = f'{login_url}?next={follow_url}'
        self.assertRedirects(response, target_url, status_code=302)

    def test_comments_login_user(self):
        post = Post.objects.create(
            text='test_text',
            author=self.author,
            group=self.group_first
        )
        self.client.post(
            reverse('add_comment', args=[post.author, post.id]),
            {'text': 'new_comment'},
            follow=True
        )
        self.assertEqual(Comment.objects.count(), 1)
        response= Comment.objects.filter(author=self.user, post=post).exists()
        print(response)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'new_comment')
        self.assertEqual(comment.author, self.user)

    def test_comment_logout_user(self):
        post = Post.objects.create(
            text='test_text',
            author=self.author,
            group=self.group_first
        )
        self.client_logout.post(
            reverse('add_comment', args=[post.author, post.id]),
            {'text': 'new_comment'},
            follow=True
        )
        self.assertEqual(Comment.objects.count(), 0)
