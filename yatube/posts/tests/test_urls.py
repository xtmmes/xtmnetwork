from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):

    user = None
    url_names = None
    templates_url_names = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ChuckNorris')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/profile.html': '/profile/ChuckNorris/',
            'posts/post_detail.html': '/posts/1/'
        }
        cls.url_names = ['/create/', '/posts/1/edit/', '/unexisting_page/']

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, address in StaticURLTests.templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_response(self):
        """URL-адрес доступен"""
        for address in StaticURLTests.templates_url_names.values():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_list_url_exists_at_desired_location(self):
        """URL-адрес доступен"""
        for address in StaticURLTests.url_names[:2]:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_added_url_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address in StaticURLTests.url_names[:2]:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, 'posts/post_create.html')

    def test_return_404(self):
        """Не существующая страница вернет ошибку 404"""
        response = self.authorized_client.get(StaticURLTests.url_names[2])
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
