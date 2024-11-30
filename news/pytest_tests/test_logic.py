from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

# Импортируем из файла с формами список стоп-слов и предупреждение формы.
# Загляните в news/forms.py, разберитесь с их назначением.
from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'

User = get_user_model()

@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(news, client, form_data):
    # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
    # предварительно подготовленные данные формы с текстом комментария.     
    url = reverse('news:detail', args=(news.id,))
    client.post(url, data=form_data)
    # Считаем количество комментариев.
    comments_count = Comment.objects.count()
    # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
    assert comments_count == 0

@pytest.mark.django_db
def test_user_can_create_comment(news, author_client, author, form_data):
    # Совершаем запрос через авторизованный клиент.
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=form_data)
    # Проверяем, что редирект привёл к разделу с комментами.
    assertRedirects(response, f'{url}#comments')
    # Считаем количество комментариев.
    comments_count = Comment.objects.count()
    # Убеждаемся, что есть один комментарий.
    assert comments_count == 1
    # Получаем объект комментария из базы.
    comment = Comment.objects.get()
    # Проверяем, что все атрибуты комментария совпадают с ожидаемыми.
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author

@pytest.mark.django_db
def test_user_cant_use_bad_words(news, author_client):
    # Формируем данные для отправки формы; текст включает
    # первое слово из списка стоп-слов.
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    # Отправляем запрос через авторизованный клиент.
    response = author_client.post(url, data=bad_words_data)
    # Проверяем, есть ли в ответе ошибка формы.
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    # Дополнительно убедимся, что комментарий не был создан.
    comments_count = Comment.objects.count()
    assert comments_count == 0

@pytest.mark.django_db
def test_author_can_delete_comment(news, comment, author_client):
    # От имени автора комментария отправляем DELETE-запрос на удаление.
    delete_url = reverse('news:delete', args=(comment.id,))
    url_redirect = reverse('news:detail', args=(news.id,))
    response = author_client.delete(delete_url)
    # Проверяем, что редирект привёл к разделу с комментариями.
    # Заодно проверим статус-коды ответов.
    assertRedirects(response, url_redirect + '#comments')
    # Считаем количество комментариев в системе.
    comments_count = Comment.objects.count()
    # Ожидаем ноль комментариев в системе.
    assert comments_count == 0

@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(comment, not_author_client):
    delete_url = reverse('news:delete', args=(comment.id,))
    response = not_author_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1

def test_author_can_edit_comment(author_client, form_data, comment, news):
    # Выполняем запрос на редактирование от имени автора комментария.
    edit_url = reverse('news:edit', args=(comment.id,))
    url_redirect = reverse('news:detail', args=(news.id,))
    response = author_client.post(edit_url, data=form_data)
    # Проверяем, что сработал редирект.
    assertRedirects(response, url_redirect + '#comments')
    # Обновляем объект комментария.
    comment.refresh_from_db()
    # Проверяем, что текст комментария соответствует обновленному.
    assert comment.text == form_data['text']

def test_user_cant_edit_comment_of_another_user(not_author_client, form_data, comment, news):
    # Выполняем запрос на редактирование от имени другого пользователя.
    edit_url = reverse('news:edit', args=(comment.id,))
    response = not_author_client.post(edit_url, data=form_data)
    # Проверяем, что вернулась 404 ошибка.
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Обновляем объект комментария.
    comment.refresh_from_db()
    # Проверяем, что текст остался тем же, что и был.
    assert comment.text == COMMENT_TEXT
