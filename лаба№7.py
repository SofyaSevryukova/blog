import requests
from bs4 import BeautifulSoup
from pprint import pprint as pp

def get_news(page_count):
    list_of_news = []
    link = 'https://news.ycombinator.com/newest'
    for j in range(page_count):
        r = requests.get(link)
        page = BeautifulSoup(r.text, 'html.parser')
        tbl_list = page.table.findAll('table')[1] #таблица с новостями
        for i in range(30):
            #заголовок новости
            title = tbl_list.findAll('a', attrs={"class": "storylink"})[i].text

            # источник новости
            find_tr = tbl_list.findAll('tr', attrs={"class": "athing"})
            if find_tr[i].findAll('span', attrs={"class": "sitestr"}):
                url = find_tr[i].findAll('span', attrs={"class": "sitestr"})[0].text
            else:
                url = None

            #количество "лайков"
            points = int(tbl_list.findAll("span", attrs={"class": "score"})[i].text.split()[0])

            #автор новости
            author = tbl_list.findAll("a", attrs={"class": "hnuser"})[i].text

            #количество комментариев
            list_a = tbl_list.findAll('td', attrs={'class': 'subtext'})[i].findAll('a')
            lenght = len(list_a)
            if list_a[lenght-1].text == 'discuss':
                comments = 0
            else:
                comments = int(list_a[lenght-1].text.split()[0])

            dict_news = {'title': title, 'author': author, 'comments': comments, 'points': points, 'url': url}
            list_of_news.append(dict_news)

        #находим следующую страницу
        #more = tbl_list.find('a', attrs={'class': 'morelink'})[0].get('href')
        more = tbl_list.find('a', attrs={'class': 'morelink'}).get('href')
        link = 'https://news.ycombinator.com/{more}'.format(more=more)

    return list_of_news

def news_list():
    s = session()
    rows = s.query(News).filter(News.label == None).all()
    return template('news_template', rows=rows)


from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, String, Integer
class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key = True)
    title = Column(String)
    author = Column(String)
    url = Column(String)
    comments = Column(Integer)
    points = Column(Integer)
    label = Column(String)

from sqlalchemy import create_engine
engine = create_engine("sqlite:///news.db")
Base.metadata.create_all(bind=engine)

from sqlalchemy.orm import sessionmaker
session = sessionmaker(bind=engine)
s = session()


##
##list_of_news=get_news(67)
###print(list_of_news)
##for one_news in list_of_news:
###for one_news in get_news(67) :    
##     news = News(title = one_news['title'],
##                 author = one_news['author'],
##                 url = one_news['url'],
##                 comments = one_news['comments'],
##                 points = one_news['points'])
##     s.add(news)
##     s.commit()



from bottle import route, run, template
from bottle import redirect, request

@route('/news')
@route('/')
def news_list():
    s = session()
    rows = s.query(News).filter(News.label == None).all()
    return template('news_template', rows=rows)


@route('/add_label/')
@route('/')
def add_label():
    s = session()
    label = request.query.label
    news_id = request.query.id
    news = s.query(News).filter(News.id == news_id).one()
    news.label = label
    s.add(news)
    s.commit()
    redirect('/news')


@route('/update_news')
@route('/')
def update_news():
    titles = []
    authors = []
    s = session()
    db_titles = s.query(News.title).all()
    db_authors = s.query(News.author).all()
    for n in range(len(db_titles)):
        titles.append(db_titles[n][0])
        authors.append(db_authors[n][0])

    # 1. Получить данные с новостного сайта
    list_of_new_news = get_news(1)

    # 2. Проверить каких новостей еще нет в БД. Будем считать,
    #    что каждая новость может быть уникально идентифицирована
    #    по совокупности двух значений: заголовка и автора
    for new_news in list_of_new_news:
        title = new_news['title']
        author = new_news['author']
        if title not in titles and author not in authors:
            news = News(title=new_news['title'],
                            author=new_news['author'],
                            url=new_news['url'],
                            comments=new_news['comments'],
                            points=new_news['points'])

    # 3. Сохранить в БД те новости, которых там нет
            s.add(news)
            s.commit()
        else:
            continue
        redirect('/news')
##run(host='localhost', port=8080)

def sort_news():
    s = session()

    news_good = s.query(News).filter(News.label == 'good').all() #сортируем все новости по отметке good
    news_maybe = s.query(News).filter(News.label == 'maybe').all()
    news_never = s.query(News).filter(News.label == 'never').all()
    p_good = len(news_good)/4035 #вероятность того, что слово относится к классу good
    p_maybe = len(news_maybe)/4035
    p_never = len(news_never)/4035

    db_titles_good = s.query(News.title).filter(News.label == 'good').all() #получаем все заголовки из бд, у которых отметка good от
    titles_good = [] #пустой списокк для заголовков
    titles_good_words = [] #пустой список для слов
    for t in range(len(db_titles_good)): 
        titles_good.append(db_titles_good[t][0]) #проходимся по каждому заголовку и берем только 1 элемент
    for g_title in range(len(db_titles_good)): # проходимся по каждому заголову из нового списка
        title_g_words = titles_good[g_title].split() # разделяем на слова
        for word in title_g_words: 
            titles_good_words.append(word) # добавляем каждой слово в список

    db_titles_maybe = s.query(News.title).filter(News.label == 'maybe').all()
    titles_maybe = []
    titles_maybe_words = []
    for l in range(len(news_maybe)):
        titles_maybe.append(db_titles_maybe[l][0])
    for m_title in range(len(titles_maybe)):
        title_m_words = titles_maybe[m_title].split()
        for word in title_m_words:
            titles_maybe_words.append(word)

    db_titles_never = s.query(News.title).filter(News.label == 'never').all()
    titles_never = []
    titles_never_words = []
    for index in range(len(news_never)):
        titles_never.append(db_titles_never[index][0])
    for n_title in range(len(titles_never)):
        title_n_words = titles_never[n_title].split()
        for word in title_n_words:
            titles_never_words.append(word)

    db_titles_without_label = s.query(News.title).filter(News.label == None).all() #проходимся по каждому названию без отметки
    db_id_without_label = s.query(News.id).filter(News.label == None).all() #берем id для новостей без отметки
    titles_without_label = [] #создадим пустой список
    for n in range(len(db_titles_without_label)): #для каждой новости без отметки
        titles_without_label.append([]) # добавляем пустой список
        titles_without_label[n].append(db_titles_without_label[n][0]) # добавляем заголовок
        titles_without_label[n].append(db_id_without_label[n][0]) # добавляем ID

    for title in range(len(titles_without_label)): 
        count_g = 0 #количество слов, встречающихся в каждом классе
        count_m = 0
        count_n = 0
        title_words = titles_without_label[title][0].split() 
        p_good_words = 0 # вероятность
        p_maybe_words = 0
        p_never_words = 0
        for word in title_words:
            for g_word in titles_good_words: # смотрим, есть ли слово в списке и, если есть, прибавляем 1
                if str(word) == str(g_word):
                    count_g += 1
                else:
                    continue

            for m_word in titles_maybe_words:
                if word == m_word:
                    count_m += 1

                else:
                    continue

            for n_word in titles_never_words:
                if word == n_word:
                    count_n += 1
                else:
                    continue

            p_good_word = count_g/(len(titles_good_words)+len(titles_maybe_words)+len(titles_never_words)) #считаем вероятность слова
            p_good_words += p_good_word # сумма вероятности всех слов
            p_maybe_word = count_m/(len(titles_good_words)+len(titles_maybe_words)+len(titles_never_words))
            p_maybe_words += p_maybe_word
            p_never_word = count_n/(len(titles_good_words)+len(titles_maybe_words)+len(titles_never_words))
            p_never_words += p_never_word

        p_new_good = p_good + p_good_words #полная вероятность отметки good
        p_new_maybe = p_maybe + p_maybe_words
        p_new_never = p_never + p_never_words

        if p_new_good >= p_new_maybe and p_new_good >= p_new_never: 
            new_label = 'new_good'
        elif p_new_maybe > p_new_good and p_new_maybe > p_new_never:
            new_label = 'new_maybe'
        else:
            new_label = 'new_never'

        news = s.query(News).filter(News.id == titles_without_label[title][1]).one() # берем новость, добавляем отметку и добавляем новость базу
        news.label = new_label
        s.commit() # сохраняем

@route('/print_news')
#@route('/')
def print_news():
    s = session()
    rows1 = s.query(News).filter(News.label == "new_good").all() 
    rows2 = s.query(News).filter(News.label == "new_maybe").all()
    rows3 = s.query(News).filter(News.label == "new_never").all()
    return template('news_template1', rows1=rows1, rows2=rows2, rows3=rows3)
run(host='localhost', port=8080)
