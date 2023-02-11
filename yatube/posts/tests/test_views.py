from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache


from ..models import Post, Group, User, Comment
from ..const import POSTS_FOR_PAGE

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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
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

        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", args=[cls.post.id]
        )
        cls.FOLLOW_URL = reverse(
            "posts:profile_follow", args=[cls.user_2.username]
        )
        cls.UNFOLLOW_URL = reverse(
            "posts:profile_unfollow", args=[cls.user_2.username]
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user_2)
        cache.clear()
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(self.user_3)
        cache.clear()

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
        ]
        for value in urls_names:
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                self.assertEqual(
                    len(response.context['page_obj']), 1
                )
                post = response.context['page_obj'][0]
                self.post_checking(post)

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
        post = response.context['post']
        self.post_checking(post)
        comments = response.context['comments'][0]
        self.comments_checking(comments)

    def check_group_not_in_mistake_group_list_page(self):
        """Проверяем чтобы созданный Пост с группой не попап в чужую группу."""
        response = self.authorized_client.get(GROUP_LIST_2_URL)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_user_cant_follow_and_unfollow(self):
        """юзер может подписываться на других юзеров
           юзер может отписаться от других юзеров"""
        follow_list_old = self.user_1.follower.count()
        self.authorized_client.get(self.FOLLOW_URL)
        follow_list_new = self.user_1.follower.count()
        self.assertEqual(follow_list_old + 1, follow_list_new)
        self.authorized_client.get(self.UNFOLLOW_URL)
        follow_list_newest = self.user_1.follower.count()
        self.assertEqual(follow_list_old, follow_list_newest)

    def test_follow_posts(self):
        """Новая запись автора появляется в ленте подписчиков,
        и не появляется в ленте подписок не подписчиков"""
        self.authorized_client.get(self.FOLLOW_URL)
        response1 = self.authorized_client.get(FOLLOW_INDEX_URL)
        post_list_old = len(response1.context['page_obj'])
        response2 = self.authorized_client3.get(FOLLOW_INDEX_URL)
        post_list_unfollower_old = len(response2.context['page_obj'])
        Post.objects.create(
            text='очередной тестовый текст',
            author=self.user_2,
            group=self.group,
        )
        response3 = self.authorized_client.get(FOLLOW_INDEX_URL)
        post_list_new = len(response3.context['page_obj'])
        response4 = self.authorized_client3.get(FOLLOW_INDEX_URL)
        post_list_unfollower_new = len(response4.context['page_obj'])
        self.assertEqual(post_list_old + 1, post_list_new)
        self.assertEqual(post_list_unfollower_old, post_list_unfollower_new)

    def test_main_page_is_cached(self):
        """главная страница кэшируется"""
        post = Post.objects.create(
            author=self.user_1,
            text="Тестовый пост",
            group=self.group,
        )
        response_first = self.guest_client.get(HOME_URL)
        post.delete()
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
        cls.author = Client()
        cls.author.force_login(cls.user)
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

    def test_count_records_at_pages(self):
        """Проверка, содержат ли страницы нужное количество записей"""
        cases = [
            (HOME_URL, POSTS_FOR_PAGE),
            (HOME_URL + '?page=2', self.ADD_SOME_POSTS),
            (GROUP_LIST_1_URL, POSTS_FOR_PAGE),
            (GROUP_LIST_1_URL + '?page=2', self.ADD_SOME_POSTS),
            (PROFILE_1_URL, POSTS_FOR_PAGE),
            (PROFILE_1_URL + '?page=2', self.ADD_SOME_POSTS)]
        for url, posts_count in cases:
            with self.subTest(url=url, posts_count=posts_count):
                self.assertEqual(
                    len(
                        self.author.get(url).context.get('page_obj')
                    ), posts_count
                )
