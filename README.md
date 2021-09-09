# media-asset-python-sdk

此SDK用于在 Python 语言中中方便的向媒体管理系统上传媒体资源。使用此SDK之前请先参考相关的 API 接口文档。

依赖安装
```
pip install -r requirements.txt
```

## 构建客户端
所有的方法都封装在 `media_asset.media_asset.MediaAsset`。构造一个`MediaAsset`的方法如下

```python
mport sys

sys.path.append(".")
from media_asset.media_asset import *

host = "119.91.67.143"
port = 80
secret_id = "secret-id"
secret_key = "secret-key"
project = 1
business = 1
service = "app-cdn4aowk"
version = "2021-02-26"

config = MediaConfig(host, port, secret_id, secret_key, project, business, service, version)

media_asset = MediaAsset(config)
```

## 获取支持媒体列表
```python

# class Category(object):
#     def __init__(self, data):
#         self.type = data["Type"]
#         self.tag_set = data["TagSet"]
#
# class Label(object):
#     def __init__(self, data):
#         self.type = data["Type"]
#         self.tag = data["Tag"]
#         self.second_tag_set = data["SecondTagSet"]
#
# category: array of Category
# Label: array if Label
# Lang: array of string
category, label, lang, response_err = media_asset.describe_categories()
print(category[0].tag_set, label[0].second_tag_set, response_err.code)
```

## 上传媒体
```python
file_path = "./test-beijingninzao-6mins.mp4" # 文件路径
media_meta = MediaMeta("视频", "新闻", "", "普通话") # 媒体元信息
media_info, response_err = media_asset.upload_file(file_path, "测试媒体", media_meta)
print(response_err.code, media_info.download_url)
```

## 获取指定媒体详细信息
```python
media_ids = [media_info.media_id] # 待查询的媒体ID列表
media_info, response_err = media_asset.describe_media_details(media_ids)
print(media_info, '\n', response_err.code)
```

## 下载媒体
```python
# 下载媒体到文件
dirs = "./" # 下载路径
filename = "test.map" # 文件名
response_err = media_asset.download_file(
    media_info.download_url,
    dirs, filename)
print(response_err.code)

# 下载媒体到内存
content, response_err = media_asset.download_file(media_info.download_url)
print(len(content), response_err.code)
```

## 获取上传媒体列表
```python
page_number = 1
page_size = 5
filter_by = FilterBy("测试", ["视频"], ["新闻"], ["上传完成"]) # 筛选参数
media_infos, total, response_err = media_asset.describe_medias(page_number, page_size, filter_by)
print(media_infos, total, response_err.code)
```

## 删除媒体
```python
# class FailedMediaInfo(object):
#     def __init__(self, data):
#         self.type = data["MediaID"]
#         self.failed_reason = data["FailedReason"]
#
# failed_media : FailedMediaInfo
failed_media, response_err = media_asset.remove_medias(media_ids)
```

## 修改媒体类型
```python
response_err = media_asset.modify_media(media_info.media_id, "综艺", "晚会")
print(response_err.code)
```

## 修改媒体过期时间
```pyton
response_err = media_asset.modify_expire_time(media_info.media_id, 1)
print(response_err.code)
```
