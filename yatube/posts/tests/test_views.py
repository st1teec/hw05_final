import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..const import POSTS_FOR_PAGE
from ..models import Comment, Follow, Group, Post, User

USERNAME_1 = "username-1"
USERNAME_2 = "username-2"
USERNAME_3 = "username-3"
SLUG_1 = "slug-1"
SLUG_2 = "slug-2"
HOME_URL = reverse("posts:main_page")
POST_CREATE_URL = reverse("posts:post_create")
LOGIN_URL = reverse("users:login")
PROFILE_1_URL = reverse("posts:profile", args=[USERNAME_1])
PROFILE2_URL = reverse("posts:profile", args=[USERNAME_2])
GROUP_LIST_1_URL = reverse(
    "posts:group_list", args=[SLUG_1]
)
GROUP_LIST_2_URL = reverse(
    "posts:group_list", args=[SLUG_2]
)
FOLLOW_INDEX_URL = reverse("posts:follow_index")
FOLLOW_URL = reverse("posts:profile_follow", args=[USERNAME_2])
UNFOLLOW_URL = reverse("posts:profile_unfollow", args=[USERNAME_2])

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create(username=USERNAME_1)
        cls.user_2 = User.objects.create(username=USERNAME_2)
        cls.user_3 = User.objects.create(username=USERNAME_3)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug=SLUG_1,
            description="Тестовое описание",
        )
        cls.group_2 = Group.objects.create(
            title="Тестовая группа",
            slug=SLUG_2,
            description="Тестовое описание",
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user_1,
            text="Тестовый пост",
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            author=cls.user_1,
            text="Тестовый коммент",
            post=cls.post
        )
        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user_1,
        )

        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", args=[cls.post.id]
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_1)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user_2)
        cls.authorized_client3 = Client()
        cls.authorized_client3.force_login(cls.user_3)

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def post_checking(self, post):
        """"метод для проверки полей поста"""
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, self.post.image)
        self.assertEqual(post.group, self.post.group)

    def comments_checking(self, comment):
        self.assertEqual(comment.text, self.comment.text)
        self.assertEqual(comment.author.username, self.comment.author.username)
        self.assertEqual(comment.post, self.comment.post)

    def test_show_correct_context(self):
        urls_names = [
            HOME_URL,
            GROUP_LIST_1_URL,
            PROFILE_1_URL,
            FOLLOW_INDEX_URL,
        ]
        for value in urls_names:
            with self.subTest(value=value):
                response = self.authorized_client2.get(value)
                self.assertEqual(
                    len(response.context['page_obj']), 1
                )
                self.post_checking(response.context['page_obj'][0])

    def test_group_list_show_correct_context(self):
        """Список постов в шаблоне group_list равен ожидаемому контексту."""
        response = self.guest_client.get(GROUP_LIST_1_URL)
        group = response.context['group']
        self.assertEqual(group, self.group)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_profile_show_correct_context(self):
        """Список постов в шаблоне profile равен ожидаемому контексту."""
        response = self.guest_client.get(PROFILE_1_URL)
        self.assertEqual(response.context['author'], self.user_1)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(self.POST_DETAIL_URL)
        self.post_checking(response.context['post'])

    def check_post_not_in_mistake_page(self):
        """созданный пост не попал в чужую группу/
        записи автора на которого пользователь не подписан
        не появляются на странице подписок."""
        urls_names = [
            GROUP_LIST_2_URL,
            FOLLOW_INDEX_URL,
        ]
        for value in urls_names:
            with self.subTest(value=value):
                self.assertNotIn(
                    self.post,
                    self.authorized_client.get(value).context['page_obj']
                )

    def test_follow(self):
        """Тест подписки на автора"""
        Follow.objects.all().delete()
        self.authorized_client.get(FOLLOW_URL)
        exist_follow = Follow.objects.filter(
            user=self.user_1,
            author=self.user_2
        ).exists
        self.assertTrue(exist_follow)

    def test_unfollow(self):
        """Тест отписки от автора"""
        Follow.objects.filter(
            user=self.user_1,
            author=self.user_2
        ).exists()
        self.authorized_client.get(UNFOLLOW_URL)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_1, author=self.user_2
            ).exists()
        )

    def test_main_page_is_cached(self):
        """главная страница кэшируется"""
        response_first = self.guest_client.get(HOME_URL)
        Post.objects.all().delete()
        response_second = self.guest_client.get(HOME_URL)
        self.assertEqual(response_first.content, response_second.content)
        cache.clear()
        response_third = self.guest_client.get(HOME_URL)
        self.assertNotEqual(response_first.content, response_third.content)


class PostsPaginatorViewsTests(TestCase):
    ADD_SOME_POSTS = 3
    ALL_POSTS = POSTS_FOR_PAGE + ADD_SOME_POSTS

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME_1)
        cls.user_2 = User.objects.create(username=USERNAME_2)
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.author_2 = Client()
        cls.author.force_login(cls.user_2)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug=SLUG_1,
            description="Тестовое описание",
        )
        Post.objects.bulk_create(
            Post(
                author=cls.user,
                text=f"Тестовый пост {i}",
                group=cls.group,
            ) for i in range(cls.ALL_POSTS))
        cache.clear()
        cls.follow = Follow.objects.create(
            user=cls.user_2,
            author=cls.user,
        )

    def test_count_records_at_pages(self):
        """Проверка, содержат ли страницы нужное количество записей"""
        cases = [
            (HOME_URL, POSTS_FOR_PAGE),
            (HOME_URL + '?page=2', self.ADD_SOME_POSTS),
            (GROUP_LIST_1_URL, POSTS_FOR_PAGE),
            (GROUP_LIST_1_URL + '?page=2', self.ADD_SOME_POSTS),
            (PROFILE_1_URL, POSTS_FOR_PAGE),
            (PROFILE_1_URL + '?page=2', self.ADD_SOME_POSTS),
            (FOLLOW_INDEX_URL, POSTS_FOR_PAGE),
            (FOLLOW_INDEX_URL + '?page=2', self.ADD_SOME_POSTS)
        ]
        for url, posts_count in cases:
            with self.subTest(url=url, posts_count=posts_count):
                self.assertEqual(
                    len(
                        self.author.get(url).context.get('page_obj')
                    ), posts_count
                )
