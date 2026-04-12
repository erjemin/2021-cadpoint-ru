from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.forms import Textarea
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from etpgrf.config import MODE_UNICODE, SANITIZE_ETPGRF
from taggit.models import Tag

from web.admin import AdminContentForm
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


class AdminTypographFormTests(SimpleTestCase):
	def test_admin_form_exposes_virtual_typograph_fields(self):
		form = AdminContentForm()

		self.assertIn('typograph_enabled', form.fields)
		self.assertIn('typograph_strip_soft_hyphens', form.fields)
		self.assertIn('typograph_mode', form.fields)
		self.assertIn('typograph_hyphenation', form.fields)
		self.assertIn('typograph_sanitizer', form.fields)
		self.assertEqual(form.fields['typograph_mode'].initial, 'mixed')
		self.assertTrue(form.fields['typograph_strip_soft_hyphens'].initial)
		self.assertTrue(form.fields['typograph_hyphenation'].initial)
		self.assertEqual(form.fields['typograph_sanitizer'].initial, 'None')

	def test_admin_form_adds_codemirror_attrs_and_media(self):
		form = AdminContentForm()

		for field_name in ('szContentHead', 'szContentIntro', 'szContentBody'):
			self.assertIsInstance(form.fields[field_name].widget, Textarea)
			self.assertEqual(
				form.fields[field_name].widget.attrs.get('data-codemirror-editor'),
				'1',
			)
			self.assertEqual(
				form.fields[field_name].widget.attrs.get('data-language'),
				'html',
			)

		self.assertIn('codemirror/editor.js', str(form.media))

	def test_tbcontent_model_has_no_btypograf_field(self):
		self.assertNotIn('bTypograf', [field.name for field in TbContent._meta.fields])

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


class AllTagsPageTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_superuser(
			username='admin',
			email='admin@example.com',
			password='password',
		)
		self.client.force_login(self.user)

		item1 = TbContent.objects.create(
			szContentHead='Тест 1',
			szContentIntro='Анонс 1',
			szContentBody='Тело 1',
			szContentSlug='test-1',
			bContentPublish=True,
		)
		item2 = TbContent.objects.create(
			szContentHead='Тест 2',
			szContentIntro='Анонс 2',
			szContentBody='Тело 2',
			szContentSlug='test-2',
			bContentPublish=True,
		)
		item1.tags.add('alpha', 'beta')
		item2.tags.add('alpha')

	def test_alltags_page_lists_all_tags_with_counts(self):
		response = self.client.get(reverse('web_alltags'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Все теги сайта')
		self.assertContains(response, '/tag_alpha')
		self.assertContains(response, '/tag_beta')
		self.assertContains(response, '<b class="_tag">2</b>')
		self.assertContains(response, '<b class="_tag">1</b>')


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
		)
		item._typograph_enabled = True

		with patch('web.models._build_typographer') as build_mock:
			build_mock.return_value.process.side_effect = lambda text: f'[{text}]'
			item.save()

		self.assertEqual(build_mock.call_count, 2)
		self.assertEqual(item.szContentHead, '[«Привет»]')
		self.assertEqual(item.szContentIntro, '[<p>Абзац</p>]')
		self.assertEqual(item.szContentBody, '[<p>Тело</p>]')

	def test_save_uses_virtual_typograph_options(self):
		item = TbContent(
			szContentHead='Привет',
			szContentIntro='Текст',
			szContentBody='Тело',
		)
		item._typograph_enabled = True
		item._typograph_mode = MODE_UNICODE
		item._typograph_hyphenation = False
		item._typograph_sanitizer = SANITIZE_ETPGRF

		with patch('web.models._build_typographer') as build_mock:
			fake_typographer = build_mock.return_value
			fake_typographer.process.side_effect = lambda text: text
			item.save()

		self.assertEqual(build_mock.call_count, 2)
		self.assertEqual(
			build_mock.call_args_list[0].kwargs,
			{
				'mode': MODE_UNICODE,
				'hyphenation': False,
				'sanitizer': SANITIZE_ETPGRF,
				'hanging_punctuation': 'left',
			},
		)
		self.assertEqual(
			build_mock.call_args_list[1].kwargs,
			{
				'mode': MODE_UNICODE,
				'hyphenation': False,
				'sanitizer': SANITIZE_ETPGRF,
				'hanging_punctuation': False,
			},
		)

	def test_save_strips_soft_hyphens_before_typograph(self):
		item = TbContent(
			szContentHead='При&shy;вет\u00ad',
			szContentIntro='А&#173;нонс',
			szContentBody='Те&shy;ло\u00ad',
		)
		item._typograph_enabled = True

		with patch('web.models._build_typographer') as build_mock:
			build_mock.return_value.process.side_effect = lambda text: f'[{text}]'
			item.save()

		self.assertEqual(build_mock.call_count, 2)
		self.assertEqual(item.szContentHead, '[Привет]')
		self.assertEqual(item.szContentIntro, '[Анонс]')
		self.assertEqual(item.szContentBody, '[Тело]')

	def test_tbcontent_has_composite_indexes_for_navigation(self):
		index_fields = [tuple(index.fields) for index in TbContent._meta.indexes]

		self.assertIn(('bContentPublish', 'tdContentPublishUp'), index_fields)
		self.assertIn(('bContentPublish', 'tdContentPublishDown'), index_fields)

	def test_show_item_increments_hits_without_touching_timestamp(self):
		item = TbContent.objects.create(
			szContentHead='Проверка просмотра',
			szContentIntro='Короткий анонс',
			szContentBody='Полный текст',
			szContentSlug='proverka-prosmotra',
			bContentPublish=True,
		)
		timestamp_before = item.dtContentTimeStamp

		response = self.client.get(f'/item/{item.id}-{item.szContentSlug}')

		self.assertEqual(response.status_code, 200)
		item.refresh_from_db()
		self.assertEqual(item.iContentHits, 1)
		self.assertEqual(item.dtContentTimeStamp, timestamp_before)


