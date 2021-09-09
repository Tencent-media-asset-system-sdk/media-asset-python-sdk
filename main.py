# -*- coding: utf-8 -*-
import sys

sys.path.append(".")
from media_asset.media_asset import *

host = "119.91.67.143"
port = 80
secret_id = "16111e9bb6ca4708abb0b4db2f"
secret_key = "fd46f3cb84c141ffa52dd9c8d6"
project = 1
business = 1
service = "app-cdn4aowk"
version = "2021-02-26"

config = MediaConfig(host, port, secret_id, secret_key, project, business, service, version)

media_asset = MediaAsset(config)

category, label, lang, response_err = media_asset.describe_categories()
print(category[0].tag_set, label[0].second_tag_set, response_err.code)

file_path = "/Users/willzhen/Desktop/视频/综艺/chunwan2020.mp4" # 文件路径
media_meta = MediaMeta("视频", "新闻", "", "普通话")
media_info, response_err = media_asset.upload_file(file_path, "测试媒体", media_meta)
if response_err.code == "ok":
  print(media_info.download_url)
else:
  print(response_err.code, response_err.message)

media_ids = [media_info.media_id] # 待查询的媒体ID列表
media_infos, response_err = media_asset.describe_media_details(media_ids)
print(media_info, '\n', response_err.code)

# 下载媒体到文件
dirs = "./" # 下载路径
filename = "test.map" # 文件名
response_err = media_asset.download_file(
    media_info.download_url,
    dirs, filename)
print(response_err.code)

# 下载媒体到内存
content, response_err = media_asset.download_t_buf(media_info.download_url)
print(len(content), ' ', response_err.code)

# 获取媒体上传列表
page_number = 1
page_size = 5
filter_by = FilterBy("测试", ["视频"], ["新闻"], ["上传完成"]) # 筛选参数
media_infos, total, response_err = media_asset.describe_medias(page_number, page_size, filter_by)
print(media_infos, total, response_err.code)

# 修改媒体类型
response_err = media_asset.modify_media(media_info.media_id, "综艺", "晚会")
print(response_err.code)

# 修改过期时间
response_err = media_asset.modify_expire_time(media_info.media_id, 1)
print(response_err.code)

# 删除媒体
# failed_media, response_err = media_asset.remove_medias(media_ids)