from django.test import TestCase
from django.urls import reverse

POST_ID = 1
USERNAME = 'username'
SLUG = 'test-slug'

ROUTES = [
    ['/', 'main_page', None],
    [f'/group/{SLUG}/', 'group_list', [SLUG]],
    [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
    [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
    ['/create/', 'post_create', None],
    [f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]],
]


class PostUrlTests(TestCase):

    def test_urls_uses_correct_route(self):
        for url, name, arg in ROUTES:
            self.assertEqual(url, reverse(f'posts:{name}', args=arg))
