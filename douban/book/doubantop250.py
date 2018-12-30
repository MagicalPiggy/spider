import requests
from requests.exceptions import RequestException
import re
import json


headers = {'User-Agent':'Mozilla/5.0(Macintosh;Intel Mac OS X 10_11_4)AppleWebKit/537.36(KHTML,like Gecko)Chrome/52.0.2743.116 Safari/537.36'}
#提取单页内容，用try，except方便找bug
def get_one_page(url):
    try:
        
        response = requests.get(url, headers=headers)#传入headers参数
        if response.status_code == 200:
            return response.text
        return response.status_code
    except RequestException:#捕获这个类型的异常
        return None


def parse_one_page(html):#定义一个函数用来解析html代码
	#生成一个正则表达式对象

	pattern = re.compile('<table.*?href.*?title="(\S+)".*?</a>.*?class.*?>(.*?)</p>.*?rating_nums">(.*?)</span>.*?</table>',re.S)

			
	items = re.findall(pattern, html)
	
	
	#items是一个list,其中的每个内容都是一个元组
	#将杂乱的信息提取并格式化，变成一个字典形式
	for item in items:
		yield { #构造一个字典
			'title': item[0],
			'imf': item[1],
			'评分': item[2],

		}

def write_to_file(content):
    #json.dumps将dict转json字符串类型；显示中文所以open中加上encoding；注意换行
    with open('doubantop250.txt', 'a', encoding='utf-8') as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')
        f.close



def main(offset):
	#url= 'http://maoyan.com/board/6?'
	url = 'https://book.douban.com/top250?start='+str(offset)
	html = get_one_page(url)
	global i
	for item in parse_one_page(html):#item是一个生成器
		print('No.',i,item)
		write_to_file(item)
		i=i+1


if __name__ == '__main__':
	i=1
	for j in range(10):
		main(j*25)