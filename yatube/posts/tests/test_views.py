from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User, Follow


class PostsViewsTests(TestCase):
    group = None
    author = None
    post = None

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
        cls.group_without_posts = Group.objects.create(
            title='Views Test',
            slug='views_slug',
            description='Views check description'
        )

        cls.template_pages_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:post_detail', args=[cls.post.id]),
            reverse('posts:post_create'),
            reverse('posts:profile', args=[cls.author.username]),
        )

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
            reverse('posts:group_list', args=[self.group_without_posts.slug])
        )
        context = response.context['page_obj'].object_list
        self.assertNotIn(self.post, context)


class PaginatorTests(TestCase):
    group = None
    user = None

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
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2',
            reverse('posts:profile',
                    kwargs={'username': self.user}) + '?page=2'
        )
        for address in addresses:
            with self.subTest(address=address):
                response = self.user_client.get(address)
                self.assertEqual(len(response.context['page_obj']), 3)


class FollowTest(TestCase):
    user = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.second_user = User.objects.create_user(username='FutureFollower')
        cls.non_follower = User.objects.create_user(username='NonFollower')
        cls.post = Post.objects.create(
            text='Post to test following.',
            author=cls.user,
        )

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.second_authorized_client = Client()
        self.non_follower_client = Client()
        self.authorized_client.force_login(self.user)
        self.second_authorized_client.force_login(self.second_user)
        self.non_follower_client.force_login(self.non_follower)

    def test_authorized_user_can_subscribe(self):
        """
        Авторизованный пользователь может подписываться на других
        пользователей.
        """
        subscribe_count = Follow.objects.count()
        self.second_authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': f'{self.post.author}'}))
        new_subscribe_count = Follow.objects.count()
        self.assertEqual(subscribe_count + 1, new_subscribe_count)

    def test_authorized_user_can_unsubscribe(self):
        """
        Авторизованный пользователь может удалять свои подписки.
        """
        Follow.objects.create(user=self.second_user, author=self.user)
        subscribe_count = Follow.objects.count()
        self.second_authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': f'{self.post.author}'}))
        new_subscribe_count = Follow.objects.count()
        self.assertEqual(subscribe_count - 1, new_subscribe_count)

    def test_author_cant_subscribe_itself(self):
        """
        Автор поста не может подписываться сам на себя.
        """
        subscribe_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': f'{self.post.author}'}))
        self.assertEqual(subscribe_count, 0)

    def test_post_appears_in_follower_list(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан.
        """
        posts_count = Post.objects.count()
        Follow.objects.create(user=self.second_user, author=self.user)
        response = self.second_authorized_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        follower_post_count = len(response.context['page_obj'].object_list)
        response_non_follower = self.non_follower_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        non_follower_post_count = len(
            response_non_follower.context['page_obj'].object_list)
        self.authorized_client.post(
            reverse('posts:post_create'),
            data={'text': 'Author created new post.'},
            follow=True
        )
        new_response = self.second_authorized_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        follower_new_post_count = len(
            new_response.context['page_obj'].object_list
        )

        self.assertEqual(posts_count, follower_post_count)
        self.assertEqual(posts_count + 1, follower_new_post_count)
        self.assertEqual(posts_count - 1, non_follower_post_count)

    def test_post_appears_not_in_user_list(self):
        response_non_follower = self.non_follower_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        new_response_non_follower = self.non_follower_client.get(
            reverse(
                'posts:follow_index'
            )
        )

        non_follower_post_count = len(
            response_non_follower.context['page_obj'].object_list)

        non_follower_new_post_count = len(
            new_response_non_follower.context['page_obj'].object_list
        )
        self.assertEqual(non_follower_post_count, non_follower_new_post_count)
