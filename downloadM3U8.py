'''
下载网页中的 m3u8 视频
'''

import requests
from bs4 import BeautifulSoup
import re
import time
import os
import urllib.parse as up
import urllib3
import random
from ffmpy3 import FFmpeg

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#TODO 需要在浏览器端自行查看 m3u8 下载的根目录
m3u8_base_url = "https://XXXX.com//m3u8/"

#TODO 网站域名
domain = 'XXXX.com'

#TODO cookie中包含用户信息, 需要在浏览器中登录后, 查看cookie, 再复制到这里。
Cookie = "username=XXX; DUID=XXX; EMAILVERIFIED=yes; school=XXX; level=XXX; CLIPSHARE=XXX"

headers = {
    'Host': domain,
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'accept-language': 'zh-CN,zh;q=0.9',
    'sec-fetch-site': 'same-origin',
    'Cookie': Cookie
}


def printTime(title, name):
    print(time.strftime('%m-%d %H:%M:%S') + " " + title + ": " + name)


def getHTML(url):
    r"""根据 url 下载网页 html 代码。若连接超时, 返回空值。

    :param url : 网页链接
    :return html : 网页html代码
    """

    for i in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=5)
            r.encoding = r.apparent_encoding
            printTime("获取 html 成功", url)
            return r.text
        except requests.exceptions.RequestException as e:
            printTime("获取 html 超时" + str(i + 1) + "次", url)
            continue
    printTime("获取 html 失败", url)
    return ""


def download(download_link, dir, file_name):
    r"""根据 url 下载文件。文件下载成功,返回True。文件下载失败,返回False。

    :param url : 文件下载地址
    :param dir : 文件本地存储路径
    :param file_name : 文件名称
    :return bool : 是否下载成功
    """

    for i in range(5):
        try:
            if not os.path.exists(dir):
                os.makedirs(dir)

            file_path = dir + file_name
            if os.path.exists(file_path):
                printTime("文件已存在", file_path)
                return False
            else:
                r = requests.get(download_link, verify=False, timeout=5)
                with open(file_path, "wb+") as f:
                    f.write(r.content)
                printTime("文件已下载", file_path)
                return True
        except requests.exceptions.RequestException as e:
            printTime("文件下载超时 " + str(i + 1) + "次", download_link)
    printTime("文件下载失败", file_path)
    return False


def m3u8ToMp4(input, output):
    r"""将 m3u8 转换成 mp4

    :param input : 文件下载地址
    :param output : 文件本地存储路径
    """

    if not os.path.exists(output):
        ff = FFmpeg(inputs={input: None}, outputs={output: None})
        ff.run()
    else:
        printTime("FFmpeg 运行失败, 文件已存在", output)


#TODO 由于 不同M3U8 有不同格式  所以这个方法不通用 需要修改代码逻辑
def downloadM3U8(download_link, dir):
    r"""根据 download_link 下载 m3u8 里的所有 ts 文件

    :param download_link : 文件下载地址
    :param dir : 文件本地存储路径
    """

    try:
        tempName = str(random.randint(10000, 99999))
        tempPath = dir + "temp\\"

        if not download(download_link, tempPath, tempName + ".m3u8"):
            return

        srcFile = tempPath + tempName + ".m3u8"

        with open(srcFile, "r") as f:
            list = f.readlines()

        # 获取视频编码
        video_encode = list[5][:-5]
        output = dir + video_encode + ".mp4"

        if os.path.exists(output):
            printTime("完整文件已下载", output)
            return

        input = tempPath + video_encode + ".m3u8"
        if not os.path.exists(input):
            os.rename(srcFile, input)

        # 获取视频中 ts 数量
        tempStr = list[len(list) - 2][:-4]
        tss = int(tempStr[len(video_encode):]) + 1

        # 下载全部 ts 文件
        for i in range(tss):
            ts_name = video_encode + str(i) + ".ts"
            ts_url = m3u8_base_url + video_encode + "/" + ts_name
            download(ts_url, tempPath, ts_name)

        m3u8ToMp4(input, output)

        os.remove(tempPath)

    except ValueError:
        printTime("m3u8 视频分析失败", download_link)


def downloadVideo(download_link, dir):
    r"""根据链接下载视频

    :param download_link : 视频下载链接
    :param dir : 视频保存路径
    """

    video_download_link = getVideoDownloadLink(download_link)

    for name, link in video_download_link.items():
        if len(link) == 0:
            continue
        elif link.find("mp4") != -1:
            download(link, dir, name + ".mp4")
        elif link.find("m3u8") != -1:
            downloadM3U8(link, dir)
        time.sleep(2)


#TODO 这个方法中的解析逻辑(正则表达式)需要依据HTML进行修改
def getVideoDownloadLink(url):
    r"""获取 视频主页链接 中的视频下载链接

    :param url : 视频主页链接
    :return video_download_link : 视频下载链接
    """

    video_download_link = {}
    for i in range(3):
        try:
            html = getHTML(url)
            if len(html) == 0:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # 获取视频名称
            video_title = soup.find_all("h4", "login_register_header")[0].text

            title = video_title.replace(" ", "")

            # 获取视频下载链接
            video_container = soup.find_all("div", "video-container")[0]
            source_pattern = re.compile(r'strencode2\(\"(.*?)\"\)')
            path = source_pattern.findall(str(video_container.contents[1]))[0]

            # url解码
            url_pattern = re.compile(r'src=\'(.*?)\'')
            ret = url_pattern.findall(up.unquote(path))[0]
            if ret.find("fdc") != -1:
                printTime("html 错误, 重新获取", ret)
                continue

            printTime("获取 视频地址 成功", ret)
            video_download_link[title] = ret
            return video_download_link

        except requests.exceptions.RequestException as e:
            printTime("连接超时", url)
            continue
        except IndexError as e:
            printTime("访问超过15次,请更新cookies", url)
            break

    printTime("获取 视频地址 失败", url)
    return video_download_link


#TODO 这个方法中的解析逻辑(正则表达式)需要依据HTML进行修改
def getVideoUrls(url):
    r"""解析网页中的视频列表, 返回所有视频的主页链接

    :param url : 视频分类列表 链接
    :return videoURL : 视频主页 链接
    """

    html = getHTML(url)
    if len(html) == 0:
        return []

    soup = BeautifulSoup(html, "html.parser")
    div_list = soup.find_all("div", "videos-text-align")
    if len(div_list) == 0:
        div_list = soup.find_all("div", "well-sm")
    if len(div_list) == 0:
        return []

    video_urls = []
    for div in div_list:
        url_pattern = re.compile(r'<a href=\"(.*?)\">')
        path = url_pattern.findall(str(div.contents[1]))[0]
        video_urls.append(path)
    return video_urls


def downloadVideoList(base_url, save_dir, page=1):
    r""" 下载 视频分类 中所有视频

    :param base_url : 网页链接
    :param save_dir : 文件保存路径
    :param page : 下载页面数量,默认为1
    """

    for page in range(1, page):

        # 生成目标页面url

        current_url = base_url + str(page)

        # 获取视频页面链接
        video_urls = getVideoUrls(current_url)
        if not len(video_urls) == 0:
            printTime("获取视频列表成功", current_url)
        else:
            printTime("获取视频列表失败", current_url)

        # 下载视频
        for url in video_urls:
            downloadVideo(url, save_dir)


def main():

    #TODO 本地下载目录
    save_dir = "F:\\XXX\\"

    # 下载 视频列表页所有视频
    url = "https://" + domain + "/XXX"
    downloadVideoList(url, save_dir, 2)

    # 根据 视频页面 下载视频
    url = "https://" + domain + "/XXXXX"
    downloadVideo(url, save_dir)

    # 根据 M3U8链接 下载视频
    url = "https://" + m3u8_base_url + "/XXXX"
    downloadM3U8(url, save_dir)


if __name__ == "__main__":
    main()
