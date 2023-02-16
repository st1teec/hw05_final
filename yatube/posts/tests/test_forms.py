import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from ..models import Comment, Group, Post, User

USERNAME = "username"
USERNAME_2 = "username2"
LOGIN_URL = reverse("users:login")
HOME_URL = reverse("posts:main_page")
POST_CREATE_URL = reverse("posts:post_create")
PROFILE_URL = reverse("posts:profile", args=[USERNAME])
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
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.another_user = User.objects.create(username=USERNAME_2)
        uploaded = SimpleUploadedFile(
            name='small0.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text="Тестовый коммент",
            post=cls.post
        )
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.REDIR_URL_EDIT = f"{LOGIN_URL}?next={cls.POST_EDIT_URL}"
        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", args=[cls.post.id]
        )
        cls.ADD_COMMENT_URL = reverse("posts:add_comment", args=[cls.post.id])
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            "text": "Какой-нибудь текст",
            "group": self.group.id,
            "image": uploaded
        }
        response = self.authorized_client.post(
            POST_CREATE_URL, data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            PROFILE_URL
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.get()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(
            post.image.name,
            Post.image.field.upload_to + form_data['image'].name
        )

    def test_guest_cant_create_post(self):
        """неавторизованный пользователь не может создать пост"""
        Post.objects.all().delete()
        form_data = {"text": "еще один текст"}
        self.guest_client.post(
            POST_CREATE_URL, data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), 0)

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()

        uploaded = SimpleUploadedFile(
            name='small1.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            "text": "Изменяем текст",
            "group": self.group_2.id,
            "image": uploaded
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            self.POST_DETAIL_URL
        )
        self.assertEqual(Post.objects.count(), posts_count)
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data["group"])
        self.assertEqual(
            post.image.name,
            Post.image.field.upload_to + form_data['image'].name
        )

    def test_guest_and_not_author_cant_edit_post(self):
        """неавторизованный пользователь и неавтор
        не может редактировать пост"""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small0.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        users_urls_list = [
            [self.guest_client, self.REDIR_URL_EDIT],
            [self.another, self.POST_DETAIL_URL],
        ]
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group.id,
            'image': uploaded,
        }
        for client, url in users_urls_list:
            with self.subTest(user=client, url=url):
                response = client.post(
                    self.POST_EDIT_URL,
                    data=form_data,
                    follow=True
                )
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.group, post.group)
                self.assertEqual(self.post.author, post.author)
                self.assertEqual(
                    post.image.name,
                    Post.image.field.upload_to + form_data['image'].name
                )
                self.assertEqual(Post.objects.count(), posts_count)
                self.assertRedirects(response, url)

    def test_create_comment(self):
        """Валидная форма создает комментарий к Post."""
        Comment.objects.all().delete()
        form_data = {
            'text': 'new_text',
        }
        response = self.another.post(
            self.ADD_COMMENT_URL,
            data=form_data,
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.get()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.another_user)
        self.assertRedirects(response, self.POST_DETAIL_URL)

    def test_guest_cant_create_comment(self):
        """неавторизованный пользователь не может оставлять комментарии"""
        Comment.objects.all().delete()
        form_data = {"text": "Тестовый коммент"}
        response = self.guest_client.post(
            self.ADD_COMMENT_URL, data=form_data, follow=True
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertFalse(
            Comment.objects.filter(
                text=form_data["text"]
            ).exists()
        )
        self.assertRedirects(
            response,
            f'{LOGIN_URL}?next={self.ADD_COMMENT_URL}'
        )
