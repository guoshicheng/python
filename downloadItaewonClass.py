'''
爬取古风动漫网的梨泰院class漫画
'''

import requests
from bs4 import BeautifulSoup
import re, time, os

headers = {
    'Host':
    'www.gufengmh8.com',
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
}

save_path = "F:\\itaewon-Class\\"


def getKeyScript(url):
    '''
    @param url : 网站url
    @return : 返回存储图片地址，下一章链接的script标签
    '''
    r = requests.get(url, headers=headers)
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, "html.parser")
    return str(soup.body.script)


def getNextChapterUrl(text):
    '''
    @param text : 古风动漫网html代码
    @return : 下一章动漫url 若没有下一章返回""
    '''
    nextChapter_pattern = re.compile(r'nextChapterData = {(.*?)};')
    nid_pattern = re.compile(r'"id":(.*?),')
    nextChapter = nextChapter_pattern.findall(text)[0]
    nid = nid_pattern.findall(nextChapter)
    if nid == "null" or nid == "":
        return ""
    else:
        return "https://www.gufengmh8.com/manhua/litaiyuanCLASS/" + nid[
            0] + ".html"


def getNextChapterTitle(text):
    '''
    @param text : 古风动漫网html代码
    @return : 下一章动漫title 若没有下一章返回""
    '''
    nextChapter_pattern = re.compile(r'nextChapterData = {(.*?)};')
    title_pattern = re.compile(r'"name":"(.*?)",')
    nextChapter = nextChapter_pattern.findall(text)[0]
    title = title_pattern.findall(nextChapter)  #需要添加try
    if title == "null" or title == "":
        return ""
    else:
        return title[0]


def getImgUrls(text):
    '''
    @param text : 古风动漫网html代码
    @return ：漫画url地址列表
    '''
    head = "https://res.xiaoqinre.com/"
    path_pattern = re.compile(r'chapterPath = \"(.*?)\";var')
    path = path_pattern.findall(text)[0]
    images_pattern = re.compile(r'chapterImages = \[(.*?)\];var')
    images = images_pattern.findall(text)[0].strip('"').split('","')
    urls = [head + path + i for i in images]
    return urls


def downloadImg(img_url, img_path, img_name):
    '''
    @param img_url : 图片url地址
    @param img_path ：图片本地存储路径
    @param img_name ：图片存储名称
    '''
    r = requests.get(img_url, verify=False)
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    with open(img_path + img_name, "wb+") as f:
        f.write(r.content)
    print(img_path + img_name)


def main():
    chapter_title = "序章-信念"

    next_chapter_html = 'https://www.gufengmh8.com/manhua/litaiyuanCLASS/1175800.html'

    while next_chapter_html:

        #获取页面关键代码
        key_script = getKeyScript(next_chapter_html)

        #获取这一章节所有图片url
        img_urls = getImgUrls(key_script)

        #遍历下载图片
        for i, url in enumerate(img_urls):
            downloadImg(url, save_path + chapter_title + "\\",
                        str(100 + i) + ".jpg")
            time.sleep(0.5)

        #获取下一章节html
        next_chapter_html = getNextChapterUrl(key_script)

        #获取下一章节title
        chapter_title = getNextChapterTitle(key_script)


if __name__ == "__main__":
    main()