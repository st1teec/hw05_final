from django.test import TestCase
from django.urls import reverse

POST_ID = 1
USERNAME = 'username'
SLUG = 'test-slug'

ROUTES = [
    ['/', 'posts:main_page', None],
    [f'/group/{SLUG}/', 'posts:group_list', [SLUG]],
    [f'/profile/{USERNAME}/', 'posts:profile', [USERNAME]],
    [f'/posts/{POST_ID}/', 'posts:post_detail', [POST_ID]],
    ['/create/', 'posts:post_create', None],
    [f'/posts/{POST_ID}/edit/', 'posts:post_edit', [POST_ID]],
    [f'/posts/{POST_ID}/comment/', 'posts:add_comment', [POST_ID]],
    ['/follow/', 'posts:follow_index', None],
    [f'/profile/{USERNAME}/follow/', 'posts:profile_follow', [USERNAME]],
    [f'/profile/{USERNAME}/unfollow/', 'posts:profile_unfollow', [USERNAME]],
]


class PostUrlTests(TestCase):

    def test_urls_uses_correct_route(self):
        for url, revers, arg in ROUTES:
            self.assertEqual(url, reverse(revers, args=arg))
