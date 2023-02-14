from django.test import TestCase

from ..models import Group, Post, User, Follow, Comment


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_2 = User.objects.create_user(username='NoName2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='просто очень длинный текст для проверки',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user_2,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='длинный тестовый комментарий более 15 символов'
        )

    def test_model_Group_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        self.assertEqual(str(self.group), self.group.title)

    def test_model_Post_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        self.assertEqual(str(self.post), self.post.text[:15])

    def test_model_Follow_have_correct_object_names(self):
        """Проверяем, что у модели Follow корректно работает __str__."""
        self.assertEqual(
            str(self.follow),
            f'Пользователь {self.follow.user} подписан на {self.follow.author}'
        )

    def test_model_Comment_have_correct_object_names(self):
        """Проверяем, что у модели Comment корректно работает __str__."""
        self.assertEqual(str(self.comment), self.comment.text[:15])
