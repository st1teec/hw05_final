from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Post, Group, User

USERNAME = "username"
SLUG = "slug"
HOME_URL = reverse("posts:main_page")
POST_CREATE_URL = reverse("posts:post_create")
LOGIN_URL = reverse("users:login")
PROFILE_URL = reverse("posts:profile", args={USERNAME})
GROUP_LIST_URL = reverse(
    "posts:group_list", args={SLUG}
)
REDIR_URL_CREATE = f"{LOGIN_URL}?next={POST_CREATE_URL}"


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = User.objects.create(username=USERNAME)
        cls.user_2 = User.objects.create(username="другой " + USERNAME)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug=SLUG,
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user_1,
            text="Тестовый пост",
        )

        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", args=[cls.post.id]
        )
        cls.REDIR_URL_EDIT = f"{LOGIN_URL}?next={cls.POST_EDIT_URL}"

    def setUp(self):
        self.guest = Client()
        self.author = Client()
        self.author.force_login(self.user_1)
        self.another = Client()
        self.another.force_login(self.user_2)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            HOME_URL: "posts/index.html",
            GROUP_LIST_URL: "posts/group_list.html",
            PROFILE_URL: "posts/profile.html",
            self.POST_DETAIL_URL: "posts/post_detail.html",
            self.POST_EDIT_URL: "posts/create_post.html",
            POST_CREATE_URL: "posts/create_post.html",
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertTemplateUsed(
                    self.author.get(template), reverse_name
                )

    def test_all_cases(self):
        """Проверка доступа к страницам для авторизованных/нет юзеров."""
        cases = [
            (HOME_URL, self.guest, 200),
            (GROUP_LIST_URL, self.guest, 200),
            (PROFILE_URL, self.guest, 200),
            (self.POST_DETAIL_URL, self.guest, 200),
            (POST_CREATE_URL, self.author, 200),
            (self.POST_EDIT_URL, self.author, 200),
            (POST_CREATE_URL, self.guest, 302),
            (self.POST_EDIT_URL, self.guest, 302),
            (self.POST_EDIT_URL, self.another, 302)]
        for url, client, status in cases:
            with self.subTest(url=url, client=client):
                self.assertEqual(client.get(url).status_code, status)

    def test_redirect_cases(self):
        """Проверка редиректа для неавториз и невавтора."""
        cases = [
            (POST_CREATE_URL, self.guest, REDIR_URL_CREATE),
            (self.POST_EDIT_URL, self.guest, self.REDIR_URL_EDIT),
            (self.POST_EDIT_URL, self.another, self.POST_DETAIL_URL)]
        for url, client, redirect in cases:
            with self.subTest(url=url, client=client, redirect=redirect):
                self.assertRedirects(client.get(url), redirect)

    def test_url_unknonw_page_return_custom_404(self):
        """проверка использования кастомного шаблона 404"""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
