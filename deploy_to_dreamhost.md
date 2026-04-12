## Установка (компиляция) версии Python 3.8.6

Проект создан на версии Python 3.8.6. Скомпилируем необходимую версию Python.

1. ВХОДИМ ЧЕРЗ SSH ЧЕРЕЗ LOGIN/PWD СВОЕГО АККАУНТА.
2. Создадим папку `tmp` (скорее всего уже создана)
3. Перейдем в эту папку
4. Скачаем tgz-архив с исходными файлами Python
5. Распакуем архив с помощью `tar`
6. Перейдем в папку `Python-3.8.6`, созданную при разархивации.
7. Сконфигурируем будущую компиляцию на размещение готовой версии Python в папку `~/opt/python-3.8.6`
8. Компилируем Python (в том числе будут запущены тесты)
9. Устанавливаем Python 3.8.6
Контакт для уведомлений: <notification_email>

```
cd ~
mkdir tmp
cd tmp
wget https://www.python.org/ftp/python/3.8.6/Python-3.8.6.tgz
tar zxvf Python-3.8.6.tgz
cd Python-3.8.6
./configure --prefix=$HOME/opt/python-3.8.6 --enable-optimizations
make
make install
```

В результате установлена нужная нам версия python установлена в папку `~/<site_root>` (`/home/<hosting_user>/opt/python-3.8.6`)

Теперь нужно назначить эту версию как `system default`, добавив к переменной `$PATH` (временно):

```
export PATH=$HOME/opt/python-3.8.6/bin:$PATH
```

------------------------------
_Также можно добавить эту строку в файл `.bashrc` и/или `.bash_profile` в домашней директории `/home/<hosting_user>`. Это нужно, чтобы сделать так, чтобы этот python всегда заменял версию которая есть на сервере._ 

-------------------------------

Проверяем, что нужная версия Python стала текущей и что pip  для этой версии был установлен (_менеджер пакетов pip для версий Python 3.x входит в поставку... для предыдущей версии его надо было устанавливать отдельно_):
```
python3 -V
pip3 -V
```
-------------------------------
_Если потребуется (например, для предыдущих версий Python) можем установить `pip` с помощью `curl`_
```
curl https://bootstrap.pypa.io/get-pip.py > ~/tmp/get-pip.py
python ~/tmp/get-pip.py
```
-------------------------------

## Настройка виртуального окружения проекта

Чтобы "заморозить" установленную версию Python в виртуальном окружении `virtualenv`:

```
pip3 install virtualenv
```

Через панель управления хостингом __Domains -> Manage Domains -> Add Hosting to a Domain/Sub-Domain__ создадим поддомен __cadpoint.ru__ (без создания нового пользователя). В нашем домашнем каталоге будет создана папка `~/<site_root>`. В этой папке будет лежать `passenger_wsgi.py`, также есть папка `public` в которой будут лежать статичные файлы не требующие обработки CGI (media, static и пр.)

Теперь создадим виртуальное окружение в папке нашего сайта (`$HOME/<site_root>`):
```
virtualenv -p python3 $HOME/<site_root>/env
```

Активируем созданное виртуальное окружение:
```
source $HOME/<site_root>/env/bin/activate
```

Проверить, что теперь мы работаем в виртуальном окружении можно дав команды:
```
python -V
pip -V
```

Мы увидим, что срабатывают нужные нам версии (т.е. не надо использовать `python3` и `pip3`).

## Установка пакетов необходимых проекту

Точный состав пакетов, обычно, находится в файле [requarement.txt](dicquo/requarement.txt). Но на всякий случай приведем список пакетов здесь (он может отличатся от действительно актуального):

~~~~~~~~~~~
| Пакет | Версия | Назначение | Зависимости |
|------|------|------|------|
| django | 3.1.3 | Фреймворк Django | притащит с собой пакеты: __asgiref-3.3.0__, __pytz-2020.4__, __sqlparse-0.4.1__
| django-taggit | 1.3.0 | Система тегов для Django | нет
| pillow | 8.0.1 | Пакет работы с графическими файлами
| pytils | 0.4.4 | Пакет рускоязычной транслитерации, работы с числительными, склонениями числительных и временными диаппазонами (для Python 3.x) | нет
| typus | 0.2.2 | типограф | нет
| urllib3 | 1.25.11 | пакет для работы с web-запросами (проекту этот пакет нужен для работы с API внешний HTML-типографов) | нет

Все эти пакеты устанавливаются в виртуальное окружение с помощью пакетного менеджера `pip`: 
```
pip install django==3.1.3
pip install django-taggit==1.3.0
pip install pillow==8.0.1
pip install pytils==0.4.4
pip install typus==0.2.2
pip install urllib3
```
~~~~~~~~~~~

Проверим, что нужная нам версия Django установилась:
```
python -c "import django; print(django.get_version())"
```

## Копируем проект на хостинг

На момент написания данной документации структура файлов и каталогов проекта в папке `cadpoint.ru` выглядела примерно так:
```
.
|-- passenger_wsgi.py
|-- cadpoint
|   |-- db.sqlite3
|   |-- manage.py
|   |-- cadpoint
|   |   |-- __init__.py
|   |   |-- asgi.py
|   |   |-- my_secret.py  # хранится только локально, в Git не коммитится
|   |   |-- settings.py
|   |   |-- urls.py
|   |   `-- wsgi.py
|   |-- templates
|   |   |-- base.html
|   |   |-- blocks
|   |   |   `-- tecnical_info.html
|   |   `-- index.html
|   `-- web
|-- public
`-- tmp
    `-- restart.txt
``` 

Далее нам надо скопировать статические файлы админки Django в папку статических файлов хостинга:
```
cd ~/<site_root>/dicquo
python manage.py collectstatic
```

## Настройка Passenger
 
Для исполнения Python на хостинге DreamHost используется CGI-механизм Passenger. Чтобы его настроить для нашего проекта в папке сайта `~/cadpoint.ru` нужно разметить файл `passenger_wsgi.py` следующего содержания ([см. документацию DreamHost](https://help.dreamhost.com/hc/en-us/articles/360002341572-Creating-a-Django-project)):

```python
#!/home/<hosting_user>/<site_root>/env/bin/python3

import sys, os
INTERP = "/home/<hosting_user>/<site_root>/env/bin/python3"
#INTERP is present twice so that the new python interpreter
#knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

cwd = os.getcwd()
sys.path.append(cwd)
sys.path.append(cwd + '/cadpoint')  #You must add your project here

sys.path.insert(0,cwd+'/env/bin')
# sys.path.insert(0,cwd+'/env/lib/python3.8/site-packages/django')
sys.path.insert(0,cwd+'/env/lib/python3.8/site-packages')

os.environ['DJANGO_SETTINGS_MODULE'] = "cadpoint.settings"
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

После этого наш сайт должен зарабоать.

Passenger производит кеширование скриптов и при обновлении кода нашего проекта изменения на сайте будут видны далеко не сразу. Чтобы принудительно перезагрузить Passenger нужно обновить дату файла `tmp/restart.txt` в папке нашего проекта ([см. документацию DreamHost](https://help.dreamhost.com/hc/en-us/articles/216385637-How-do-I-enable-Passenger-on-my-domain-)). 

Сначала создадим соответствующий каталог:
```
cd ~/cadpoint.ru
mkdir -p tmp
```

Обновлять `restart.txt` можно командой:
```
touch ~/cadpoint.ru/tmp/restart.txt
```

## Дополнительно

Стоит включить ssl-сертификат для сайта. В панели управления DreamHost __Domains --> SSL/TLS Certificates__
