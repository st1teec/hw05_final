from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post, User

USERNAME = "username"
USERNAME_2 = "username2"
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


class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username=USERNAME)
        cls.another_user = User.objects.create(username=USERNAME_2)
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
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text="Тестовый коммент",
            post=cls.post
        )
        cls.POST_EDIT_URL = reverse("posts:post_edit", args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse(
            "posts:post_detail", args=[cls.post.id]
        )
        cls.ADD_COMMENT_URL = reverse("posts:add_comment", args=[cls.post.id])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another = Client()
        self.another.force_login(self.another_user)

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
        self.assertTrue(
            str(form_data['image']).split('.')[0] in str(post.image.file)
        )

    def test_guest_cant_create_post(self):
        """неавторизованный пользователь не может создать пост"""
        Post.objects.all().delete()
        posts_count = Post.objects.count()
        form_data = {"text": "еще один текст"}
        response = self.guest_client.post(
            POST_CREATE_URL, data=form_data, follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertNotContains(response, form_data['text'])

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()

        uploaded = SimpleUploadedFile(
            name='small.gif',
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
        self.assertTrue(
            str(form_data['image']).split('.')[0] in str(post.image.file)
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_cant_edit_post(self):
        """неавторизованный пользователь не может редактировать пост"""
        posts_count = Post.objects.count()
        clients = (
            self.guest_client,
            self.another
        )
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group.id,
        }
        for client in clients:
            with self.subTest(user=client):
                client.post(
                    self.POST_EDIT_URL,
                    data=form_data,
                    follow=True
                )
                post = Post.objects.get(id=self.post.id)
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.group, post.group)
                self.assertEqual(self.post.author, post.author)
                self.assertEqual(Post.objects.count(), posts_count)

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
        comments_count = Comment.objects.count()
        form_data = {"text": "Тестовый коммент"}
        response = self.guest_client.post(
            self.ADD_COMMENT_URL, data=form_data, follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertNotContains(response, form_data['text'])
