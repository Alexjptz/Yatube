from django.test import Client, TestCase
from django.urls.base import reverse

from posts.models import User


class Test_user(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'testuser'
        self.password = '12qwerty12'

    def test_registration(self):
        response = self.client.post(
            reverse('signup'),
            {'username': self.username, 'password': self.password},
            follow=True
            )
        self.assertEqual(
            response.status_code,
            200,
            msg='проверь регистрацию пользователя'
            )
