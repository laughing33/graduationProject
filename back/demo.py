# -*- coding:utf-8-*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import urllib2
import json
from random import shuffle
import multiprocessing
import gensim
import csv

# 所有歌单song2Vec模型的训练和保存
def train_song2vec():
    songlist_sequence = []
    # 读取网易云音乐原数据
    for i in range(1, 5176):
        with open("data/{0}.json".format(i), 'r') as load_f:
            load_dict = json.load(load_f)
            parse_songlist_get_sequence(load_dict, songlist_sequence)

    # 多进程计算
    cores = multiprocessing.cpu_count()
    print('Using all {cores} cores'.format(cores=cores))
    print('Training word2vec model...')
    model = gensim.models.Word2Vec(sentences=songlist_sequence, size=150, min_count=3, window=7, workers=cores)
    print('Save model..')
    model.save('songVec.model')



    # 解析每个歌单中的歌曲id信息
    # load_dict: 包含一个歌单中所有歌曲的原始列表
    # songlist_sequence: 一个歌单中所有给的id序列
def parse_songlist_get_sequence(load_dict, songlist_sequence):


    song_sequence = []
    for item in load_dict['playlist']['tracks']:
        try:
            song = [item['id'], item['name'], item['ar'][0]['name'], item['pop']]
            song_id, song_name, artist, pop = song
            song_sequence.append(str(song_id))
        except:
            print('song format error')

    for i in range(len(song_sequence)):
        shuffle(song_sequence)
        # 这里的list()必须加上，要不songlist中歌曲根本就不是随机打乱序列，而是都相同序列
        songlist_sequence.append(list(song_sequence))


    # 歌曲id到歌曲名字的映射
    # 歌曲id到歌曲名字的映射字典，歌曲名字到歌曲id的映射字典
def song_data_preprocessing():

    csv_reader = csv.reader(open('data/neteasy_song_id_to_name_data.csv'))
    id_name_dic = {}
    name_id_dic = {}
    for row in csv_reader:
        id_name_dic[row[0]] = row[1]
        name_id_dic[row[1]] = row[0]
    return id_name_dic, name_id_dic

# 读取网页，获取接口数据
def down1(url):
    return urllib2.urlopen(url).read()

# 预先登录，调取用户数据
url = "http://192.168.3.2:3000/v1/login/cellphone?phone=17772002134&password=614919799"
down1(url)
# 获取用户收藏的歌曲，以此来推荐歌曲
url = "http://192.168.3.2:3000/v1/likelist?uid=645954254"
song_id_list = down1(url)[down1(url).find('[') + 1:down1(url).find(']')].split(',')


# 训练模型
train_song2vec()

model_str = 'songVec.model'
# 载入word2vec模型
model = gensim.models.Word2Vec.load(model_str)
id_name_dic, name_id_dic = song_data_preprocessing()

# 接收所推荐的歌曲以及其相似度
# [('4237923', 0.9994074702262878), ('411349945', 0.9994284510612488),
#  ('17381310', 0.9994289875030518), ('1436753138', 0.9994584918022156)]
rec_songs=[]

# 提取rec_songs里面的歌曲id进行推荐
# ['4237923', '411349945', '17381310', '1436753138']
recommend_songs=[]
for song_id in song_id_list:
    result_song_list = model.most_similar(song_id)
    # song_id_list是用户喜欢的歌曲
    # result_song_list是根据某一首歌推荐的十首歌
    print(song_id)
    # 提取相似度最高的歌曲
    rec_songs.append(result_song_list[0])
    print(json.dumps(id_name_dic[song_id], encoding='UTF-8', ensure_ascii=False))
    print('\n相似歌曲和相似度分别为：')
    for song in result_song_list:
        print(json.dumps(id_name_dic[song[0]], encoding='UTF-8', ensure_ascii=False))
        print(song[0])
        print(song[1])
        # print('\t' + id_name_dic[song[0]].encode('utf-8'), song[1])
    print('\n')

# 对推荐的歌曲id进行提取，舍弃相似度
for s in rec_songs:
    recommend_songs.append(s[0])
# recommend_songs是所推荐的歌曲


# 读取txt里的歌曲id放入数组
data = []
for line in open("data/songs.txt","r"):
    data.append(line)
# 将之前所推荐的歌曲从推荐歌单中删除
for s in data:
    url="http://192.168.3.2:3000/v1/playlist/tracks?op=del&pid=4982171318&tracks="+s
    down1(url)

# 将每次所推荐的歌曲id写入txt中，方便下次将其删除，每次都是先删除昨天的，再推荐今天的
filename = 'data/songs.txt'
for s in recommend_songs:
    with open(filename, 'a') as file_object:
        file_object.write(s+"\n")
    url = "http://192.168.3.2:3000/v1/playlist/tracks?op=add&pid=4982171318&tracks="+s
    down1(url)
