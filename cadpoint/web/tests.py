from django.test import SimpleTestCase

from web.legacy_links import build_canonical_url, replace_legacy_links


class LegacyLinksTests(SimpleTestCase):
	def test_build_canonical_url_without_slug(self):
		self.assertEqual(build_canonical_url(123, ''), '/item/123-')

	def test_replace_legacy_links_rewrites_internal_urls(self):
		text = (
			'<a href="/news/1-latest-news/123-old-title.html">link</a>'
			'<a href="http://www.cadpoint.ru/component/content/article/456-some-article.html">x</a>'
			'<a href="https://example.com/news/1-latest-news/123-old-title.html">external</a>'
		)
		new_text, matches = replace_legacy_links(text, {123: 'new-title', 456: 'article-title'})

		self.assertIn('/item/123-new-title', new_text)
		self.assertIn('/item/456-article-title', new_text)
		self.assertIn('https://example.com/news/1-latest-news/123-old-title.html', new_text)
		self.assertEqual(len(matches), 2)

	def test_replace_legacy_links_does_not_touch_image_urls(self):
		text = (
			'<a href="/news/1-latest-news/123-old-title.html">link</a>'
			'<img src="/images/stories/news/photo123.jpg" alt="photo">'
		)
		new_text, matches = replace_legacy_links(text, {123: 'new-title'})

		self.assertIn('/item/123-new-title', new_text)
		self.assertIn('/images/stories/news/photo123.jpg', new_text)
		self.assertEqual(len(matches), 1)

