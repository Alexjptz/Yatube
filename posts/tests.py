from django.contrib.auth.models import AnonymousUser
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Comment, Group, Post, User


class TestPostsApp(TestCase):
    def setUp(self):
        self.client_anon = Client()
        self.client_auth = Client()
        self.author = User.objects.create(username='PinkFloyd')
        self.group = Group.objects.create(
            title='Have a cigar',
            slug='Wish_you_were_here'
        )
        self.text = 'By the way, which one is Pink'
        self.client_auth.force_login(self.author)
        cache.clear()

    def prepare_post_pages(self):
        post = Post.objects.create(
            text=self.text,
            author=self.author,
            group=self.group
        )
        pages = (
            reverse('index'),
            reverse('profile', args=[self.author.username]),
            reverse('post', args=[self.author.username, post.id]),
            reverse('group', args=[post.group.slug]),
            )
        return post, pages

    def test_profile(self):
        response = self.client_anon.get(
            reverse('profile', args=[self.author.username])
        )
        self.assertEqual(
            response.status_code,
            200,
            msg='проверь страницу профайла пользователя'
            )

    def test_anononymos_new_post(self):
        posts_now = Post.objects.count()
        response = self.client_anon.post(
            reverse('new_post'),
            {'text': self.text, 'group': self.group, 'author': AnonymousUser}
        )
        url = f"{reverse('login')}?next={reverse('new_post')}"
        post_after = Post.objects.count()
        with self.subTest():
            self.assertRedirects(
                response,
                url,
                msg_prefix='Проверь переадрисацию если анон не создает поста'
            )
        with self.subTest():
            self.assertEqual(
                posts_now,
                post_after,
                msg='Анноним не должен создавать пост, проверь'
            )

    def test_user_new_post(self):
        data = {'text': self.text, 'group': self.group.id}
        posts_now = Post.objects.count()
        response = self.client_auth.post(
            reverse('new_post'),
            data,
            folow=True)
        posts_after = Post.objects.count()
        post = Post.objects.get(pk=1)
        self.assertNotEqual(
            posts_now,
            posts_after,
            msg='Пост не записывается в базу'
        )
        self.assertEqual(
            response.status_code,
            302,
            msg='редирект не работает'
        )
        # self.assertEqual(
        #     self.author,
        #     post.author,
        #     msg='Поле author в базу записано не верно'
        # )
        # self.assertEqual(
        #     self.group,
        #     post.group,
        #     msg='Поле группа в базу записано не верно'
        # )
        # self.assertEqual(
        #     self.text,
        #     post.text,
        #     msg='Поле text в базу записано не верно'
        # )

    def test_post_exists_at_pages(self):
        post, pages = self.prepare_post_pages()
        for page in pages:
            with self.subTest():
                response = self.client_auth.get(page)
                self.assertEqual(
                    response.status_code,
                    200,
                    msg=f'{page} работает не правильно, проверь'
                )
                if 'paginator' in response.context:
                    self.assertEqual(
                        response.context['paginator'].count,
                        1
                    )
                    self.assertIn(
                        post,
                        response.context['paginator'].object_list,
                        msg=f'Пост отсутствует в {page} Paginator, проверь'
                    )
                else:
                    self.assertEquals(
                        post.author,
                        response.context['post'].author,
                        msg=f'Пост отсутствует в context {page}'
                    )
                    self.assertEquals(
                        post.group,
                        response.context['post'].group,
                        msg=f'Пост отсутствует в context {page}'
                    )
                    self.assertEquals(
                        post.author,
                        response.context['post'].author,
                        msg=f'Пост отсутствует в context {page}'
                    )

    def test_post_edit(self):
        post, pages = self.prepare_post_pages()
        posts_now = Post.objects.all().count()
        group = Group.objects.create(title='NewGroup', slug='NewGroup')
        data = {
            'text': 'New Test Text',
            'group': group.id
        }
        response = self.client_auth.post(
            reverse('post_edit', args=[self.author, post.id]),
            data,
            follow=True)
        posts_after = Post.objects.all().count()
        post.refresh_from_db()
        self.assertEqual(
            posts_now,
            posts_after,
            msg='Создается новый пост, а должен редактироваться'
        )
        self.assertEqual(
            response.status_code,
            200,
            msg='Проверь переадресацию после редактирования поста'
        )
        for page in pages:
            print(page)
            print(response.context)
            with self.subTest(page=page):
                response = self.client_auth.get(page)
                self.assertEqual(
                    response.status_code,
                    200,
                    msg=f'{page} работает не правильно, проверь'
                )
                if 'paginator' in response.context:
                    print(response.context['paginator'].object_list)
                    self.assertEqual(
                        response.context['paginator'].count,
                        1,
                        msg='В paginator пусто'
                    )
                    self.assertIn(
                        post,
                        response.context['paginator'].object_list,
                        msg=f'Пост отсутствует в {page} Paginator, проверь'
                    )
                else:
                    self.assertEquals(
                        post.author,
                        response.context['post'].author,
                        msg=f'Пост отсутствует в context {page}'
                    )
                    self.assertEquals(
                        post.group,
                        response.context['post'].group,
                        msg=f'Пост отсутствует в context {page}'
                    )
                    self.assertEquals(
                        post.author,
                        response.context['post'].author,
                        msg=f'Пост отсутствует в context {page}'
                    )

    def test_post_image_tag(self):
        with open('media/posts/1.jpg', 'rb') as img:
            response = self.client_auth.post(reverse('new_post'), {
                'text': 'post with image',
                'image': img},
                follow=True
            )
            self.assertContains(response, '<img')

    def test_image_tags_in_pages(self):
        post, pages = self.prepare_post_pages()
        with open('media/posts/1.jpg', 'rb') as img:
            response = self.client_auth.post(
                reverse('post_edit', args=[post.author, post.id]), {
                    'author': self.author,
                    'group': self.group.id,
                    'text': 'post with image',
                    'image': img
                    },
                follow=True
            )
        for page in pages:
            response = self.client_auth.get(page)
            with self.subTest('Тега нет на странице ' + page):
                self.assertContains(response, '<img')

    def test_upload_not_img(self):
        with open('media/posts/not_image_file.txt', 'rb') as img:
            response = self.client_auth.post(reverse('new_post'), {
                'author': self.author,
                'group': self.group.id,
                'text': 'post with image',
                'image': img},
                follow=True
            )
        self.assertFormError(
             response,
             'form',
             'image',
             'Загрузите правильное изображение. '
             'Файл, который вы загрузили, '
             'поврежден или не является изображением.'
        )

    def test_index_cache(self):
        response_1 = self.client_auth.get(reverse('index'))
        Post.objects.create(
            author=self.author,
            group=self.group,
            text=self.text,
        )
        response_2 = self.client_auth.get(reverse('index'))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.client_auth.get(reverse('index'))
        self.assertNotEqual(response_1.content, response_3.content)

    def test_auth_user_comment(self):
        post, pages = self.prepare_post_pages()
        self.client_auth.post(reverse(
            'add_comment',
            args=[
                post.author,
                post.id]),
            {'text': 'Коммент'},
            follow=True)
        self.assertEqual(Comment.objects.count(), 1)

    def test_auth_user_subscribe(self):
        author = User.objects.create(username='NewAuthor')
        self.client_auth.post(reverse(
            'profile_follow',
            args=[author.username])
        )
        response_follow = self.client_auth.get(
            reverse('profile', args=[author.username])
        )
        self.client_auth.post(
            reverse('profile_unfollow', args=[author.username])
        )
        response_unfollow = self.client_auth.get(
            reverse('profile', args=[author.username])
        )
        with self.subTest():
            self.assertTrue(
                response_follow.context['subscribe'],
                msg='Не удается подписаться на автора'
            )
        with self.subTest():
            self.assertFalse(
                response_unfollow.context['subscribe'],
                msg='Не удается отписаться от автора'
            )

    def test_follow_index(self):
        author = User.objects.create(username="NewAuthor")
        post = Post.objects.create(
            text=self.text,
            author=author,
            group=self.group
        )
        user_1 = User.objects.create(username="newUser")
        user_2 = User.objects.create(username="newUser2")
        self.client_auth.force_login(user_1)
        self.client_auth.post(
            reverse('profile_follow', args=[author.username])
        )
        response_1 = self.client_auth.get(
            reverse('follow_index')
        )
        self.client_auth.force_login(user_2)
        response_2 = self.client_auth.get(
            reverse('follow_index')
        )
        self.assertIn(post, response_1.context['paginator'].object_list)
        self.assertNotIn(post, response_2.context['paginator'].object_list)


class TestServerResponses(TestCase):
    def setUp(self):
        self.client_anon = Client()

    def test_404(self):
        url = "/daglkdjnglkjfadg/"
        response = self.client_anon.get(url)
        self.assertEqual(
            response.status_code,
            404,
            msg='Страница 404 не работает'
        )
