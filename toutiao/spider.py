import  requests
from urllib.parse import urlencode
from requests.exceptions import RequestException
import json
from bs4 import BeautifulSoup
import re
from config import *
import  pymongo
import os
from hashlib import md5
from multiprocessing import Pool
from json.decoder import JSONDecodeError
from pathlib import Path

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
#声明mongodb数据库对象
client = pymongo.MongoClient(MONGO_URL,connect=False)
db = client[MONGO_DB]

#请求索引页（索引页中包含着许多图集的url）
def get_page_index(offset,keyword):
    data = {#定义一个data字典，用于Ajax请求
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': '3',
        'from': 'gallery'
    }
    url='http://www.toutiao.com/search_content/?'+urlencode(data)
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求索引页出错')
        return None


#传入索引页的html，解析出每个图集的url
def parse_page_index(html):
    try:#加入异常处理
        data = json.loads(html)#对html进行解析，转换为字典。

        if data and 'data' in data.keys():#data.keys()返回的是这个json的所有的键名，这里判断'data'在这些键名中
            for item in data.get('data'):#data对应还有许多值，遍历这些值

                yield item.get('article_url')#构造一个生成器，取出data中的每一个article_url对应的url


    except JSONDecodeError:
        print('解析异常')

#请求每个图集的详情页
def get_page_detail(url):
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求详情页出错',url)
        return None

#解析详情页，获取图集中每张图片的url
def parse_page_detail(html,url):
    soup = BeautifulSoup(html, 'lxml')
    # 用BeautifulSoup来提取title信息
    title = soup.select('title')[0].get_text()
    print(title)
    #下面提取json串，串中包含了图片信息
    images_pattern = re.compile('JSON.parse\("(.*?)"\),', re.S)#注意对括号进行转义
    result=re.search(images_pattern,html)
    if result:
        result = result.group(1).replace('\\', '')
        data = json.loads(result)#转换成json对象
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            #每个sub_images都是一个字典，需要遍历它来提取url元素
            # 用一句话来构造一个list，把item赋值为sub_images的每一个子元素
            # 再取得sub_images的每一个item对象的url属性，完成列表的构建，这个列表名为images，里面是sub_images下所有的url
            images = [item.get('url') for item in sub_images]
            root_dir=create_dir(PATH_NAME+KEYWORD)
            download_dir = create_dir(root_dir/title)
            for image in images: download_image(download_dir,image)#通过循环把图片下载下来
            return {#以一个字典形式返回
                'title':title,
                'url':url,#这是当前详情页的url
                'images':images
            }

#把url存储到数据库
def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('存储到MongoDB成功',result)
        return  True
    return False

#通过url来请求图片
def download_image(save_dir,url):
    print('正在下载',url)
    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            save_image(save_dir,response.content)#content返回的是二进制内容，一般处理图片都用二进制流
            return response.text
        return None
    except RequestException:
        print('请求图片出错',url)
        return None

def create_dir(name):
    #根据传入的目录名创建一个目录，这里用到了 python3.4 引入的 pathlib 。
    directory = Path(name)
    if not directory.exists():
         directory.mkdir()
    return directory

def save_image(save_dir,content):
    file_path = '{0}/{1}.{2}'.format(save_dir,md5(content).hexdigest(),'jpg')
    if not os.path.exists(file_path):#如果文件不存在
        with open(file_path,'wb') as f :
            f.write(content)
            f.close()

def main(offset):
    html=get_page_index(offset, KEYWORD)
    for url in parse_page_index(html):#获得每个图集的url
         print(url)
         html=get_page_detail(url)#用某个图集的url来请求详情页
         if html:
            result=parse_page_detail(html,url)#解析详情页的信息
            if result:save_to_mongo(result)





if __name__ == '__main__':

    groups = [x*20 for x in range(GROUP_START,GROUP_END+1)]#20,40,60...
    pool=Pool()
    pool.map(main,groups)