import json
import requests
import time
from multiprocessing  import Pool
from datetime import datetime
from pandas.tseries.offsets import DateOffset
import argparse

parser = argparse.ArgumentParser()
now = datetime.now()
stopdate = str(now - DateOffset(months=12))[:10]

parser.add_argument('-P', '--posts', help='-P for posts method', action='store_const', const='Posts')
parser.add_argument('-D', '--dates', help='-D for dates method', action='store_const', const='Dates')
parser.add_argument('-s','--stopdate', type=str, help="Date %d_%m_%Y", default=stopdate)
parser.add_argument('-v', '--values', type=int, help="Number of posts to download", default=300)

args = parser.parse_args()


# надо достать ссылки
with open('links_instagram.txt', 'r', encoding='utf-8') as file:
    data = file.read()
urls = data.split('\n')
print(len(urls))
print(urls[0])

parametr = args.values
end_date = args.stopdate # в формате 2020-05-13 str
metka = True # чтобы остановить программу по дате нужна в функциях likes_comments_request_1 и give_likes_comments

def date_to_timestamp(date):
    date = date + '-0-0-0-0-0-0'
    date = date.split('-')
    date = [int(i) for i in date]
    timestamp = time.mktime(tuple(date))
    date = float(repr(timestamp))
    return date

def date_from_timestamp(timestamp):
    #timestamp = timestamp
    value = datetime.fromtimestamp(timestamp)
    date = value.strftime('%Y-%m-%d')
    
    return date

def likes_comments_request_media(json_page):
    global artists_likes_comments
    global end_date
    end_date_timestamp = date_to_timestamp(end_date)
    imiges = json_page['data']['user']['edge_owner_to_timeline_media']['edges']
    
    
    for i in range(len(imiges)):
        shortcode = imiges[i]['node']['shortcode']
        timestamp = imiges[i]['node']['taken_at_timestamp']
        date = date_from_timestamp(timestamp)# получаю дату из timestamp в посте
        
        if int(timestamp) < end_date_timestamp:# + 86400, чтобы дата была включительно
            global metka
            metka = False
            break
        
        likes = imiges[i]['node']['edge_media_preview_like']['count']
        comments = imiges[i]['node']['edge_media_to_comment']['count']
        # если видео
        views = 0
        if imiges[i]['node']['is_video'] == True:
            
            #video = imiges[i]['node']['thumbnail_resources']['video_view_count']
            views = imiges[i]['node']['video_view_count']

        artist_likes_comments = {'id' : shortcode,'date': date,'likes': likes, 'comments' : comments, 'views': views}
        artists_likes_comments.append(artist_likes_comments)
    #print(artists_likes_comments)

    
def likes_comments_request_1(json_page):
    global artists_likes_comments
    global end_date
    #print(end_date)
    end_date_timestamp = date_to_timestamp(end_date)
    #print(end_date_timestamp)
    imiges = json_page['graphql']['user']['edge_owner_to_timeline_media']['edges']
    
    
    for i in range(len(imiges)):
        shortcode = imiges[i]['node']['shortcode']
        timestamp = imiges[i]['node']['taken_at_timestamp']
        date = date_from_timestamp(timestamp)# получаю дату из timestamp в посте
        #print(date,'-')
        if int(timestamp) < end_date_timestamp:# + 86400, чтобы дата была включительно
            global metka
            metka = False
            break
        
        likes = imiges[i]['node']['edge_media_preview_like']['count']
        comments = imiges[i]['node']['edge_media_to_comment']['count']
        # если видео
        views = 0
        if imiges[i]['node']['is_video'] == True:
            #video = imiges[i]['node']['thumbnail_resources']['video_view_count']
            views = imiges[i]['node']['video_view_count']
        #print(date,'--')
        artist_likes_comments = {'id' : shortcode,'date': date, 'likes': likes, 'comments' : comments, 'views': views}
        artists_likes_comments.append(artist_likes_comments)
    #print(artists_likes_comments)

def give_likes_comments(url):
    url_a1 = url+'/?__a=1'
    print(url_a1)
    global artists_likes_comments
    global metka
    #artists_likes_comments = []
    #r = requests.get('https://www.instagram.com/arianagrande/?__a=1')
    #print(url_a1)
    r = requests.get(url_a1)

    if r.text != '{}':
        b = json.loads(r.text)
        # достанем значения количества комментариев и лайков


        json_page = json.loads(r.text)
        likes_comments_request_1(json_page)
        user_id = b['graphql']['user']['id']
        end_cursor = b['graphql']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
        #13я первая
        print(end_cursor)
        if end_cursor != None:
            i = 1
            while True:
                link = 'https://instagram.com/graphql/query/?query_id=17888483320059182&id={user_id}&first=12&after={end_cursor}'.format(user_id=user_id,end_cursor=end_cursor)
                r = requests.get(link)
                b = json.loads(r.text)
                likes_comments_request_media(b)
                end_cursor = b['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
                global parametr
                print(parametr)
                print(end_cursor)
                print(link)
                print(i)
                i+=1
                if (i*12 >= parametr) or (end_cursor == None) or (metka == False):
                    break
                    
        artists_likes_comments = artists_likes_comments[0:parametr]    
        return artists_likes_comments
    else:
        return [{'likes':0,'comments':0,'views':0}]

def main_f(url):
    global artists_likes_comments
    artists_likes_comments = []
    artists_likes_comments = give_likes_comments(url)
    #print('ctr',artists_likes_comments[0])
    # надо посчитать сумму
    sum_likes = 0
    sum_comments = 0
    sum_views = 0
    for i in artists_likes_comments:
        sum_likes += i['likes']
        sum_comments += i['comments']
        sum_views += i['views']
    print(url.split('.com/')[-1])
    print(sum_likes)
    print(sum_comments)
    print(sum_views)

    artist_stat = {
        'name artist' : url, 
        'array' : artists_likes_comments,
        'sum likes'  : sum_likes,
        'sum comments' : sum_comments,
        'sum views' : sum_views
    }

    with open('res_inst\\proverka3--{}.json'.format(url.split('.com/')[-1]), 'w') as f:
        json.dump(artist_stat, f)
        
if __name__ =='__main__':
    for i in range(2,100):
        print('pack = ',i,'\n======================================================\n======================================================\n======================================================\n')
        urls_min = urls[i*100:i*100+100]
        pool = Pool(5) # сделаем number_of_threads параллельных процессов
        start_time = time.time()
        results = pool.map(main_f, urls_min)
        pool.close()
        pool.join()
        #for url in urls[30:]:
        #    main_f(url)
        print('время: ', time.time()-start_time)
