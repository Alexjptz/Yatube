import shutil

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User

TEST_DIR = 'test_data'


@override_settings(MEDIA_ROOT=(TEST_DIR + '/media'))
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

    def prepare_post_pages(self, group):
        post = Post.objects.create(
            text=self.text,
            author=self.author,
            group=self.group
        )
        pages = (
            reverse('index'),
            reverse('profile', args=[self.author.username]),
            reverse('post', args=[self.author.username, post.id]),
            reverse('group', args=[group.slug]),
            )
        return post, pages

    def upload_img_file(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        file = SimpleUploadedFile(
            'small.jpg',
            content=small_gif,
            content_type='image/jpg'
        )
        return file

    def post_testing_pages_content(self, post, pages):
        for page in pages:
            with self.subTest(page=page):
                response = self.client_anon.get(page)
                self.post_content_page_test(response, post)

    def post_content_page_test(self, response, post):
        self.assertEqual(
            response.status_code,
            200,
            msg='Страница работает не правильно, проверь'
        )
        if 'paginator' in response.context:
            self.assertEqual(
                response.context['paginator'].count,
                1,
                msg='В paginator пусто'
            )
            post_at_page = response.context['page'][0]
        else:
            post_at_page = response.context['post']
        self.assertEquals(
            post.author,
            post_at_page.author,
            msg='Несоответствие в поле author'
        )
        self.assertEquals(
            post.group,
            post_at_page.group,
            msg='Несоответствие в поле group'
        )
        self.assertEquals(
            post.text,
            post_at_page.text,
            msg='Несоответствие в поле text'
        )

    def test_profile(self):
        response = self.client_anon.get(
            reverse('profile', args=[self.author.username])
        )
        self.assertEqual(
            response.status_code,
            200,
            msg='проверь страницу профайла пользователя'
            )

    def test_anonymous_new_post(self):
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
        response = self.client_auth.post(
            reverse('new_post'),
            data,
            follow=True)
        self.assertEqual(
            Post.objects.count(),
            1,
            msg='Пост не записывается в базу'
        )
        post = Post.objects.last()
        self.assertEqual(
            response.status_code,
            200,
            msg='редирект не работает'
        )
        self.assertEqual(
            self.author,
            post.author,
            msg='Проверь поле author'
        )
        self.assertEqual(
            self.group,
            post.group,
            msg='Проверь поле group'
        )
        self.assertEqual(
            self.text,
            post.text,
            msg='Проверь поле text'
        )

    def test_post_exists_at_pages(self):
        post, pages = self.prepare_post_pages(self.group)
        self.post_testing_pages_content(post, pages)

    def test_post_edit(self):
        group = Group.objects.create(title='NewGroup', slug='NewGroup')
        post, pages = self.prepare_post_pages(group)
        posts_now = Post.objects.count()
        data = {
            'text': 'New Test Text',
            'group': group.id
        }
        response = self.client_auth.post(
            reverse('post_edit', args=[self.author, post.id]),
            data,
            follow=True
        )
        posts_after = Post.objects.count()
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
        self.post_testing_pages_content(post, pages)

    def test_image_tag_in_pages(self):
        post, pages = self.prepare_post_pages(self.group)
        file = self.upload_img_file()
        data = {
            'author': self.author,
            'group': self.group.id,
            'text': 'with image',
            'image': file
        }
        response = self.client_auth.post(
            reverse('post_edit', args=[post.author, post.id]),
            data,
            follow=True
        )
        for page in pages:
            with self.subTest('Тега нет на странице ' + page):
                response = self.client_anon.get(page)
                self.assertContains(response, '<img')

    def test_upload_not_img(self):
        file = SimpleUploadedFile(
            'Image.jpg',
            content=b'TextText',
            content_type='image/jpg'
        )
        data = {
            'author': self.author,
            'group': self.group.id,
            'text': 'with image',
            'image': file
        }
        response = self.client_auth.post(
            reverse('new_post'),
            data,
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
        self.assertEqual(
            Post.objects.count(),
            0,
            msg='Запись не должна добовляться, проверь'
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
        post, pages = self.prepare_post_pages(self.group)
        data = {'text': 'Коммент'}
        self.client_auth.post(
            reverse('add_comment', args=[post.author, post.id]),
            data,
            follow=True
        )
        self.assertEqual(
            Comment.objects.count(),
            1,
            msg='Запись не комментируется'
        )
        comment = Comment.objects.first()
        self.assertEqual(
            comment.text,
            data['text'],
            msg='Проверь текст комментария'
        )
        self.assertEqual(
            comment.author,
            post.author,
            msg='Проверь автора комментария'
        )
        self.assertEqual(
            comment.post,
            post,
            msg='Комментарий не соответствует записи'
        )

    def test_anon_user_comment(self):
        post, pages = self.prepare_post_pages(self.group)
        data = {'text': 'Коммент'}
        self.client_anon.post(reverse(
            'add_comment',
            args=[
                post.author,
                post.id]),
            data,
            follow=True)
        self.assertEqual(
            Comment.objects.count(),
            0,
            msg='Не авторизированный пользователь может комментировать'
        )

    def test_auth_user_subscribe(self):
        author = User.objects.create(username='NewAuthor')
        self.client_auth.post(reverse(
            'profile_follow',
            args=[author.username])
        )
        self.assertEqual(
            Follow.objects.count(),
            1
        )
        self.assertTrue(
            Follow.objects.filter(user=self.author, author=author),
            msg='Не удается подписаться на пользователя'
        )

    def test_auth_user_unsubscribe(self):
        author = User.objects.create(username='NewAuthor')
        Follow.objects.create(
            user=self.author,
            author=author
        )
        self.client_auth.post(
            reverse('profile_unfollow', args=[author.username])
        )
        self.assertEqual(
            Follow.objects.count(),
            0,
            msg='Не удается отписаться на пользователя'
        )

    def test_follow_index_of_subscribed_user(self):
        post, pages = self.prepare_post_pages(self.group)
        author = User.objects.create(username="NewAuthor")
        Follow.objects.create(
            user=author,
            author=self.author
        )
        self.client_auth.force_login(author)
        response = self.client_auth.get(reverse('follow_index'))
        self.post_content_page_test(response, post)

    def test_follow_index_of_unsubscribed_user(self):
        post, pages = self.prepare_post_pages(self.group)
        user_1 = User.objects.create(username='NewUser_1')
        user_2 = User.objects.create(username='NewUser_2')
        Follow.objects.create(
            user=user_1,
            author=self.author
        )
        self.client_auth.force_login(user_2)
        response = self.client_auth.get(reverse('follow_index'))
        self.assertEqual(
            response.context['paginator'].count,
            0,
            msg='Запись появляется на странице подписок'
        )


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


def tearDownModule():
    print('\nDeleting temporary files...\n')
    try:
        shutil.rmtree(TEST_DIR)
    except OSError:
        pass
