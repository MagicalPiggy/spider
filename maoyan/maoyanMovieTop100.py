import requests
from requests.exceptions import RequestException
import re
import json
from multiprocessing import Pool
 
headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.5514.400 QQBrowser/10.1.1660.400'}
 
#提取单页内容，用try，except方便找bug
def get_one_url(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求页面失败')
        return None
 
#解析
def parse_one_page(html):
    try:
        #注意正则换行，匹配结果类型是list；尽量匹配到要提取的目标的name
        pattern = re.compile('<dd>.*?board-index.*?>(\d+)</i>.*?data-src="(.*?)".*?name">.*?>(.*?)</a>'
                             + '.*?star">(.*?)</p>.*?releasetime">(.*?)</p>.*?integer">(.*?)</i>'
                             + '.*?fraction">(.*?)</i>', re.S)
        items = re.findall(pattern, html)
        #注意用for循环将list变成dict，把return变成一个generator更清晰明了
        for item in items:
            yield{
                'number' : item[0],
                'img' : item[1],
                'title' : item[2].strip(),
                'actor' : item[3].strip()[3:],
                'releasetime' : item[4].strip()[5:],
                'scoore' : item[5] + item[6]
                }
    except Exception:
        print('解析错误')
        return None
 
#保存
def write_to_file(content):
    #json.dumps将dict转json字符串类型；显示中文所以open中加上encoding；注意换行
    with open('maoyanMovieTop100_result.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close
 
def main(offset):
    url = 'http://maoyan.com/board/4?offset=' + str(offset)
    html = get_one_url(url)
    contents = parse_one_page(html)
    for i_content in contents:
        print(i_content)
        write_to_file(i_content)
 
if __name__ == '__main__':
    #实现多进程提高效率；map函数的使用后面的参数用中括号转成一个list
    pool = Pool()
    pool.map(main, [i * 10 for i in range(10)])
