# conftest.py
import pytest

# Импортируем класс клиента.
from django.test.client import Client
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from datetime import datetime, timedelta 

# Импортируем модель заметки, чтобы создать экземпляр.
from news.models import News, Comment

User = get_user_model()

@pytest.fixture
# Используем встроенную фикстуру для модели пользователей django_user_model.
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):  
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def author_client(author):  # Вызываем фикстуру автора.
    # Создаём новый экземпляр клиента, чтобы не менять глобальный.
    client = Client()
    client.force_login(author)  # Логиним автора в клиенте.
    return client


@pytest.fixture
def not_author_client(not_author):
    client = Client()
    client.force_login(not_author)  # Логиним обычного пользователя в клиенте.
    return client


@pytest.fixture
def news():
    news = News.objects.create(  # Создаём объект новость.
        title='Новость',
        text='Текст новости',
    )
    return news

@pytest.fixture
def news_and_comments():
    author = User.objects.create(username='Комментатор')
    news = News.objects.create(  # Создаём объект новость.
        title='Новость',
        text='Текст новости',
    )
    now = timezone.now()
    # Создаём комментарии в цикле.
    for index in range(10):
        # Создаём объект и записываем его в переменную.
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        # Сразу после создания меняем время создания комментария.
        comment.created = now + timedelta(days=index)
        # И сохраняем эти изменения.
        comment.save()
    return news

@pytest.fixture
def all_news():
    today = datetime.today()
    all_news = [
        News(title=f'Новость {index}',
             text='Просто текст.',
             date=today - timedelta(days=index)
             )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)
    return all_news


@pytest.fixture
def comment(author, news):
    comment = Comment.objects.create(  # Создаём объект комментарий.
        text='Текст комментария',
        news=news,
        author=author,
    )
    return comment

@pytest.fixture
# Фикстура запрашивает другую фикстуру создания заметки.
def pk_for_args(news):  
    # И возвращает pk новости.
    # На то, что это кортеж, указывает запятая в конце выражения.
    return (news.pk,)

@pytest.fixture
def form_data():
    return {
        'text': 'Текст комментария',
        'news': 'news',
        'author': 'Комментатор',
    }
