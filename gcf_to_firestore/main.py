#!/usr/bin/env python

# ADCで解決*できる場合(サービスアカウントキーを指定しない)これだけでも良さそう
from google.cloud import firestore
# db = firestore.Client() こちらを各メソッドで呼び出してる
# `pip install google-cloud-firestore` でinstall すると使える


# *ADCで解決
# 事前に export GOOGLE_APPLICATION_CREDENTIALS="[PATH]" でサービスアカウントkeyを登録しておく必要があり

import os
import base64, hashlib, hmac
import datetime
import logging

from flask import abort, jsonify

#CLIコマンド用
import fire

# default_collection: str = 'Users'
default_collection: str = 'Expenses'
default_sort_key: str = 'date'
PROJECT = os.environ.get('PROJECT')


from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)

def usage():
    return '''Usage:
food <cost> {<comment>}
cons <cost> {<comment>}
tran <cost> {<comment>}
dura <cost> {<comment>}
acti  <cost> {<comment>}
heal <cost> {<comment>}
ls {<YY/MM>}
sum {<YY/MM>}
del <uniq id>'''

# For Function framework
def hello_debug(req):
    '''#You can test in `curl localhost:8080 -X POST -d 'food 77'`
    #Returnがないとエラーになる。printはlogが出力されてるところで確認できるはず'''
    print('start*********************')
    text = req.get_data(as_text=True)
    print(text,'\n\n')
    return 'testtest'



# ADC設定しとけばいらない。key直接指定の場合
# def _auth():
#     import firebase_admin
#     from firebase_admin import credentials
#     from firebase_admin import firestore #ADCで解決できる場合いらない
#     cred = credentials.Certificate("/Users/taro/Downloads/pjname-firebase-adminsdk-1cqak-f61136c234.json")
#     firebase_admin.initialize_app(cred)


# # Add or Update document
def add(collection=default_collection,
    type='', cost=0, comment='', user_id='test太郎'):
    '''Add document. See more `$ ./firestore_sample.py add -h`'''
    print('insert start to firestore*****************')
    if type.lower() in 'food':
        type = 'food'
    elif type.lower() in 'cons':
        type = 'consumables'
    elif type.lower() in 'tran':
        type = 'transportation'
    elif type.lower() in 'acti':
        type =  'activity'
    elif type.lower() in 'dura':
        type =  'durables'
    elif type.lower() in 'heal':
        type = 'healthcare'

    db = firestore.Client(project=PROJECT)
    d = {
        'cost': cost,
        'type': type,
        'date': firestore.SERVER_TIMESTAMP,#datetime.datetime.now(),#UTCで登録される str(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
        'comment': comment,
        'user_id': user_id
    }

    # Generate random Document ID
    try:
        res = db.collection(collection).add(d)
        document_id = res[1].id
        print(f'Created Doc Id: {document_id}')
    except Exception as e:
        print(e)
        return e

    return document_id

# read collection
def read(collection=default_collection, sort_key=default_sort_key):
    '''Read collection.
    # クエリタイプがたくさんある
    https://qiita.com/subaru44k/items/a88e638333b8d5cc29f2#%E3%83%87%E3%83%BC%E3%82%BF%E3%81%AE%E6%A4%9C%E7%B4%A2%E3%81%A8%E5%8F%96%E5%BE%97
    https://qiita.com/subaru44k/items/a88e638333b8d5cc29f2#%E3%82%AF%E3%82%A8%E3%83%AA%E3%82%BF%E3%82%A4%E3%83%97
    '''
    # _auth()
    db = firestore.Client(project=PROJECT)

    # docs = db.collection('users').get() #stream()でも取れる。違いは？
    col_ref = db.collection(collection)
    docs_query = col_ref.order_by(sort_key).limit_to_last(50) #新しい順
    print(f'[+] Display list {collection}')
    
    for doc in docs_query.get():
        print(doc.id, doc.to_dict())
        # print(doc.get('date').strftime('%Y-%m-%d %H:%M:%S'))

    # 比較演算子は、以下が使用可能。
    # <、<=、==、>、>=
    # where()メソッドをつなげることで、AND条件検索が実行可能。
    # colRef.where("state", "==", "CO").where("name", "==", "Denver")
    # ただし、等価比較の==と範囲比較の<, <=, >, >=を組み合わせる場合はカスタムインデックスを作成しておく必要がある。
    # エラーの際のログに設定用のURLが含まれるようなので、一度エラー出しておいてURLから設定でも良さそう
    
        # print('name:{} age:{}'.format(
        #     doc.get('name'), doc.get('age')))
        # # print(doc.to_dict())
        # print(f'{doc.id} => {doc.to_dict()}\n\n')


def ls_by_month(yyyy_slash_mm='2021/11'): #Return -> Document snapshots.
    #yyyy/mmに紐づくデータを取ってくる
    print('Execute a query to firestore *******************')
    import calendar
    items = []
    db = firestore.Client(project=PROJECT)

    yyyy = int(yyyy_slash_mm.split('/')[0])
    mm = int(yyyy_slash_mm.split('/')[1])

    print(yyyy, mm, sep='***')

    start = datetime.datetime(yyyy, mm, 1)
    print(yyyy, mm, sep='***')

    if mm == 12:
        mm = 0
        yyyy += 1

    print(yyyy, mm, sep='***')
    end = datetime.datetime(yyyy, mm+1, 1)
    # end = datetime.datetime(yyyy, mm, calendar.monthrange(yyyy, mm)[1]) # これだと、 「... <= 2022-01-31 00:00:00」 となって 1/31の12:00とかのデータは取れない

    print(f'{start} to {end}')

    # docs = db.collection(default_collection).order_by("date").get()#end_at(datetime.datetime.now()).get()
    # docs = db.collection(default_collection).get()
    docs = db.collection(default_collection).where('date', '<', end).where('date', '>=', start).get()

    # print(f'docs.exist: {type(docs)}')
    # for doc in docs:
    #     print(doc.to_dict())# {'comment': 'コメント', 'type': 'food', 'cost': 100, 'user_id': 'test太郎', 'date': DatetimeWithNanoseconds(2021, 11, 17, 2, 34, 15, 595000, tzinfo=datetime.timezone.utc)}
    
    return docs

def _update(collection=default_collection, doc_id=''):
    # 未実装
    db = firestore.Client(project=PROJECT)
    #n Updaten and Delete
    user_ref = db.collection(collection).document('Doc_id_of_taro')
    user_ref.update({'age': 15})
    #新規でフィールド追加する場合
    user_ref.update({'Hight': 175})
    user_ref.update({'timestamp': firestore.SERVER_TIMESTAMP})
    #フィールド削除 存在しないとエラーになる
    # user_ref.delete('tall')

    datatypes = {
    u'stringExample': u'Hello, World!',
    u'booleanExample': True,
    u'numberExample': 3.14159265,
    u'dateExample': datetime.datetime.now(),
    u'arrayExample': [5, True, u'hello'],
    u'nullExample': None,
    u'objectExample': {
        u'a': 5,
        u'b': True
        }
    }
    db.collection(u'data').document(u'one').set(datatypes)

class Delete(object):
    '''See more `$ ./firestore_sample.py Delete -h`'''
    def __init__(self, size=1000):
        self.db = firestore.Client(project=PROJECT)
        self.batch_size = size

    def doc(self, collection=default_collection, doc_id=''):
        '''警告: ドキュメントを削除しても、そのドキュメントのサブコレクションは削除されません。
        '''
        ret = self.db.collection(collection).document(doc_id).delete()
        # breakpoint()
        print(f'[+] Delete Doc_id: {doc_id} complete')
        return ret #Datetimeが返ってくる。存在しないidでも

    def all(self, collection):
        '''--sizeで件数を指定できるよ。
        firebase firestore:delete [options] <<path>> でも削除できるよ
        https://firebase.google.com/docs/firestore/manage-data/delete-data?hl=ja#collections'''
        docs = self.db.collection(collection).limit(self.batch_size).stream()
        deleted = 0

        print('ほんとに全部削除していいの？？')
        breakpoint()

        for doc in docs:
            print(f'Deleting doc {doc.id} => {doc.to_dict()}')
            doc.reference.delete()
            deleted = deleted + 1

        if deleted >= self.batch_size:
            return all(collection)

def parse_data(text):
    import re
    from datetime import datetime

    reg_insert = re.compile('^(food|cons|tran|acti|heal|dura)\s(\d+)\s?([\d\w]+)?$', flags=re.IGNORECASE)
    reg_ls = re.compile('^ls\s?(\d{2}/\d{2})?$', flags=re.IGNORECASE)
    reg_sum = re.compile('^sum\s?(\d{2}/\d{2})?$', flags=re.IGNORECASE)
    reg_del = re.compile('^del\s([\w\d\-]+)$', flags=re.IGNORECASE)

    if reg_insert.match(text) is not None:
        parsed = reg_insert.match(text).groups()
        return parsed[0], parsed[1], parsed[2]
    elif reg_sum.match(text) is not None:
        parsed = reg_sum.match(text).groups()
        if parsed[0] is None:
            print('current month')
            return 'sum', datetime.strftime(datetime.today(), '%Y/%m'), 'dummy'
        else:
            print('specific month')
            return 'sum', "20{}".format(parsed[0]), 'dummy'
    elif reg_ls.match(text) is not None:
        parsed = reg_ls.match(text).groups()
        if parsed[0] is None:
            print('current month')
            return 'ls', datetime.strftime(datetime.today(), '%Y/%m'), 'dummy'
        else:
            print('specific month')
            return 'ls', "20{}".format(parsed[0]), 'dummy'
    elif reg_del.match(text) is not None:
        parsed = reg_del.match(text).groups()
        return 'del', parsed[0], 'dummy'
    else:
        return 'unknown' , 'dummy', 'dummy'

def ls_handler(value='2999/01'):
    print('ls *******************', value)
    docs = ls_by_month(value)
    reply = f'{value}\n\n' 
    temp = []
    for doc in docs:
        d = doc.to_dict()
        mm_yy_time = d.get('date').astimezone().strftime('%Y-%m-%d %H:%M:%S')[0:-3]
        cmnt = d.get('comment')
        # breakpoint()
        if cmnt:
            temp.append("{},{}:{} {}\n".format(mm_yy_time, d['type'], d['cost'], cmnt))
        else:
            temp.append("{},{}:{}\n".format(mm_yy_time, d['type'], d['cost']))
    temp = sorted(temp, reverse=True)

    for r in temp:
        reply += r

    return reply

def sum_handler(value='2999/01'):
    print('sum *******************')
    from collections import Counter, defaultdict
    d = defaultdict(int)
    d_cnt = defaultdict(int)
    total = 0

    docs = ls_by_month(value)
    reply = '{}\n\n'.format(value)

    for doc in docs:
        r = doc.to_dict()
        d[r['type']] += int(r['cost'])
        d_cnt[r['type']] += 1
        total += int(r['cost'])

    tpl = sorted(d.items(), key=lambda x:x[1], reverse=True)

    for k,v in tpl:
        reply += '{}({}):{}\n'.format(k, d_cnt[k], v)

    reply += '====================\nTotal:{}'.format(total)
    return reply


def delete_hander(value='xx'):
    print(f'{"="*15} collection: {default_collection}, value: {value} {"="*15}')
    # ret = Delete.doc(doc_id = value) #これはエラーになる
    dd = Delete(size=10)
    ret = dd.doc(doc_id = value)


# Functionsにデプロイされると勝手にこれが付く挙動 # from flask import abort, jsonify
def fujiko3(request):
    channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
    channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

    line_bot_api = LineBotApi(channel_access_token)
    parser = WebhookParser(channel_secret)

    body = request.get_data(as_text=True)
    hash = hmac.new(channel_secret.encode('utf-8'),
        body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash).decode()

    if signature != request.headers['X_LINE_SIGNATURE']:
        return abort(405)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        return abort(405)

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        
        text = event.message.text
        # schema: https://developers.line.biz/ja/reference/messaging-api/#webhook-event-objects
        # 上通りで辞書で取得すると、取れなかった。user_id = event.source.get('userId')
        # line sdkのクラスだけどuserIdでも取れなかった。****** user id: <class 'linebot.models.sources.SourceUser'> {"type": "user", "userId": "xxx"}
        # https://line-bot-sdk-python.readthedocs.io/en/stable/_modules/linebot/models/sources.html#SourceUser
        # 上のドキュメントで user_idとなってたので以下で取れた。
        # print('****** user id:', type(event.source), event.source.user_id)
        _user_id = event.source.user_id

        _type, _value, _comment = parse_data(text); #取得される_valueはモード(ls,sum etc)による

        if _type == 'ls':
            reply = ls_handler(_value)
        elif _type == 'sum':
            reply = sum_handler(_value)
        elif _type == 'del':
            delete_hander(_value)
            reply = f'多分、削除できたよ: {_value}'
        elif _type == 'unknown':
            reply = usage()
        else:
            docid = add(collection='Expenses', type=_type, cost=_value, comment=_comment, user_id=_user_id)
            reply = f'{docid}'

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply.rstrip())
            # TextSendMessage(text=event.message.text)
        )
    return jsonify({ 'message': 'ok'})



if __name__ == '__main__':
    fire.Fire()
