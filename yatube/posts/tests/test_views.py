from django import forms
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User, Follow


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='views_author')
        cls.group = Group.objects.create(
            title='Views Title',
            slug='views_group',
            description='Views description',
        )
        cls.post = Post.objects.create(
            text='Views text',
            author=cls.author,
            group=cls.group
        )
        cls.group_check = Group.objects.create(
            title='Views Test',
            slug='views_slug',
            description='Views check description'
        )
        cls.template_pages_names = {
            '/': 'posts/index.html',
            '/group/views_group/': 'posts/group_list.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{cls.post.id}/edit/': 'posts/post_create.html',
            '/profile/views_user/': 'posts/profile.html',
        }

    def setUp(self):
        self.user = User.objects.create_user(username='views_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post(self, post):
        """Набор служебных assert."""
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username,
                         self.post.author.username)
        self.assertEqual(post.group.title, self.group.title)
        self.assertEqual(post.pk, self.post.pk)

    def test_homepage_shows_correct_context(self):
        """Index получает соответствующий контекст."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.check_post(post)

    def test_group_list_context(self):
        """Group_list получает соответствующий контекст."""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.group.slug])
        )
        group = response.context.get('group')
        self.assertEqual(group.title,
                         self.group.title)
        self.assertEqual(group.description,
                         self.group.description)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.pk, self.group.id)

    def test_profile_show_correct_context(self):
        """Profile получает соответствующий контекст."""
        response = self.authorized_client.get(
            reverse('posts:profile', args=[self.author.username])
        )
        post = response.context['page_obj'][0]
        self.check_post(post)

    def test_post_detail_show_correct_context(self):
        """Post_detail получает соответствующий контекст."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[self.post.id])
        )
        self.assertEqual(response.context.get('post').id, self.post.id)

    def test_create_post_correct_context(self):
        """Post_create получает соответствующий контекст."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_appearance(self):
        """Проверка вывода новой записи на всех страницах."""
        response = self.authorized_client.get(reverse('posts:index'))
        object_on_main_site = response.context['page_obj'][0]
        self.assertEqual(object_on_main_site, self.post)
        response = self.authorized_client.get(
            reverse('posts:group_list', args=['views_group'])
        )
        post = response.context['page_obj'][0]
        response = self.authorized_client.get(
            reverse('posts:profile', args=[self.author.username])
        )
        self.assertEqual(post, self.post)
        context = {
            response.context['page_obj'][0]: self.post,
            post.group: self.group,
        }
        for element, names in context.items():
            with self.subTest(element=element):
                self.assertEqual(element, names)

    def test_post_not_found(self):
        """Проверка отсутствия записи в лишней группе"""
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.group_check.slug])
        )
        context = response.context['page_obj'].object_list
        self.assertNotIn(self.post, context)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовая группа',
        )
        for cls.post in range(10 + 3):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        addresses = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        )
        for address in addresses:
            with self.subTest(address=address):
                response = self.user_client.get(address)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_posts(self):
        addresses = (
            reverse('posts:index') + '?page=2',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2',
            reverse('posts:profile', kwargs={'username': self.user}) + '?page=2'
        )
        for address in addresses:
            with self.subTest(address=address):
                response = self.user_client.get(address)
                self.assertEqual(len(response.context['page_obj']), 3)