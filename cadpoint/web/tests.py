from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from taggit.models import Tag

from web.add_function import clean_text_to_slug, safe_html_special_symbols
from web.legacy_links import build_canonical_url, replace_legacy_links
from web.models import TbContent


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


class SafeHtmlSpecialSymbolsTests(SimpleTestCase):
	def test_strips_html_tags_and_decodes_entities(self):
		text = '<p>&laquo;Привет&nbsp;<b>мир</b>&raquo; &shy;<script>alert(1)</script><style>p{}</style></p>'


		self.assertEqual(safe_html_special_symbols(text), '«Привет мир»')

	def test_clean_text_to_slug_normalizes_non_latin_symbols(self):
		self.assertEqual(clean_text_to_slug('αβγ ΔΩ'), 'content')
		self.assertEqual(clean_text_to_slug('₽ € $ ₴ ₿'), 'content')

	def test_tbcontent_str_uses_clean_text(self):
		item = TbContent(id=7, szContentHead='<b>&laquo;Привет&nbsp;мир&raquo;</b>')

		self.assertEqual(str(item), '007: «Привет мир»')


class TagAutocompleteTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_superuser(
			username='admin',
			email='admin@example.com',
			password='password',
		)
		Tag.objects.create(name='alpha')
		Tag.objects.create(name='beta')
		Tag.objects.create(name='gamma')
		self.client.force_login(self.user)

	def test_returns_tag_results_for_term(self):
		response = self.client.get(
			reverse('web_tag_autocomplete'),
			{'term': 'al'},
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload['pagination']['more'], False)
		self.assertEqual([item['text'] for item in payload['results']], ['alpha'])

	def test_returns_initial_tag_batch_without_term(self):
		response = self.client.get(reverse('web_tag_autocomplete'))

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(len(payload['results']), 3)
		self.assertEqual(payload['pagination']['more'], False)

	def test_paginates_tag_results(self):
		Tag.objects.all().delete()
		for index in range(30):
			Tag.objects.create(name=f'tag-{index:02d}')

		response = self.client.get(reverse('web_tag_autocomplete'), {'page': 1})
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(len(payload['results']), 25)
		self.assertEqual(payload['pagination']['more'], True)

		response = self.client.get(reverse('web_tag_autocomplete'), {'page': 2})
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(len(payload['results']), 5)
		self.assertEqual(payload['pagination']['more'], False)


class TypographTests(TestCase):
	def test_save_generates_slug_from_clean_text(self):
		item = TbContent(szContentHead='<b>Привет&nbsp;мир</b>')

		item.save()

		self.assertEqual(item.szContentSlug, 'privet-mir')

	def test_save_normalizes_non_latin_slug_to_default(self):
		item = TbContent(szContentHead='αβγ ΔΩ')

		item.save()

		self.assertEqual(item.szContentSlug, 'content')

	def test_save_uses_etpgrf_and_clears_flag(self):
		item = TbContent(
			szContentHead='«Привет»',
			szContentIntro='<p>Абзац</p>',
			szContentBody='<p>Тело</p>',
			bTypograf=True,
		)

		with patch('web.models._TYPOGRAPHER_HEAD.process') as head_process_mock, \
			 patch('web.models._TYPOGRAPHER_TEXT.process') as text_process_mock:
			head_process_mock.side_effect = lambda text: f'HEAD[{text}]'
			text_process_mock.side_effect = lambda text: f'TEXT[{text}]'
			item.save()

		self.assertEqual(head_process_mock.call_count, 1)
		self.assertEqual(text_process_mock.call_count, 2)
		self.assertEqual(item.szContentHead, 'HEAD[«Привет»]')
		self.assertEqual(item.szContentIntro, 'TEXT[<p>Абзац</p>]')
		self.assertEqual(item.szContentBody, 'TEXT[<p>Тело</p>]')
		self.assertFalse(item.bTypograf)


