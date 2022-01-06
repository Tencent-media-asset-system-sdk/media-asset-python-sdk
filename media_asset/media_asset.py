#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import json
import enum
import hashlib
import requests
import grequests
from retrying import retry

import sys

sys.path.append(".")
from .tisign.sign import *

class MediaState(enum.Enum):
  UPLOADING = "上传中"
  WAITINGVERIFY = "等待验证"
  COMPLETED = "上传完成"
  FAILED = "上传失败"
  DOWNLOADING = "下载素材中"
  VERIFYING = "验证素材中"
  DELETED = "素材已删除"
  CLEANED = "素材已清理"
  
  @classmethod
  def contains_value(cls, v):     # 判断是否包含某个值
    return v in cls._value2member_map_

class MediaLang(enum.Enum):
  MANDARIN = "普通话"
  CANTONESE = "粤语"
  
  @classmethod
  def contains_value(cls, v):     # 判断是否包含某个值
    return v in cls._value2member_map_


class MediaSecondTag(enum.Enum):
  EVENING = "晚会"
  OTHER = "其他"
  
  @classmethod
  def contains_value(cls, v):     # 判断是否包含某个值
    return v in cls._value2member_map_

class MediaTag(enum.Enum):
  NEWS = "新闻"
  ENTERTAINNENT = "综艺"
  INTERNETINFO = "互联网资讯"
  MOVIE = "电影"
  SERIES = "电视剧"
  SPECIAL = "专题"
  SPORT = "体育"
  
  @classmethod
  def contains_value(cls, v):     # 判断是否包含某个值
    return v in cls._value2member_map_


class MediaType(enum.Enum):
  VIDEO = "视频"
  LIVE = "直播流"
  IMAGE = "图片"
  AUDIO = "音频"
  TEXT = "文稿"
  
  @classmethod
  def contains_value(cls, v):     # 判断是否包含某个值
    return v in cls._value2member_map_

class MediaResponse(object):
    def __init__(self, data):
        self.request_id = data.get("RequestID", "")
        self.code = "ok"
        self.message = "success"
        if "Error" in data:
            self.code = data["Error"]["Code"]
            self.message = data["Error"]["Message"]


class MediaConfig(object):
    def __init__(self, host, port, secret_id, secret_key, project, business, service, version):
        self.host = host
        self.port = port
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.project = project
        self.business = business
        self.service = service
        self.version = version


class MediaMeta(object):
    def __init__(self, media_type, media_tag, media_second_tag, media_lang):
        self.media_type = media_type
        self.media_tag = media_tag
        self.media_second_tag = media_second_tag
        self.media_lang = media_lang

    def to_map(self):
        return {
            "MediaType": self.media_type,
            "MediaTag": self.media_tag,
            "MediaSecondTag": self.media_second_tag,
            "MediaLang": self.media_lang
        }


class Category(object):
    def __init__(self, data):
        self.type = data["Type"]
        self.tag_set = data["TagSet"]


class Label(object):
    def __init__(self, data):
        self.type = data["Type"]
        self.tag = data["Tag"]
        self.second_tag_set = data["SecondTagSet"]


class FilterBy(object):
    def __init__(self, media_name_or_id, media_type_set, media_tag_set, status_set):
        self.media_name_or_id = media_name_or_id
        self.media_type_set = media_type_set
        self.media_tag_set = media_tag_set
        self.status_set = status_set

    def to_map(self):
        return {
            "MediaNameOrID": self.media_name_or_id,
            "MediaTypeSet": self.media_type_set,
            "MediaTagSet": self.media_tag_set,
            "StatusSet": self.status_set
        }


class FailedMediaInfo(object):
    def __init__(self, data):
        self.type = data["MediaID"]
        self.failed_reason = data["FailedReason"]

class UploadMedia(object):
    def __init__(self, name, local_path, media_url, media_meta, md5):
        self.name = name # 名字
        self.local_path = local_path # 服务器路径，不是用本地路径传入空
        self.media_url = media_url # 网路地址
        self.media_meta = media_meta # 媒体信息
        self.md5 = md5 # md5，不使用传空

    def to_map(self):
        return {
            "Name": self.name,
            "LocalPath": self.local_path,
            "MediaURL": self.media_url,
            "MediaMeta": self.media_meta.to_map(),
            "ContentMD5": self.md5
        }
    
    def to_json(self):
        return json.dumps(self.to_map)

class UploadMediaInfo(object):
    def __init__(self, data):
        self.media_id = data["MediaID"]
        self.failed_reason = data["FailedReason"]
    
    def to_map(self):
        return {
            "MediaID": self.media_id,
            "FailedReason": self.failed_reason
        }

class MediaInfoSet(object):
    def __init__(self, data):
        self.media_id = data.get("MediaID", 0)
        self.name = data.get("Name", "")
        self.duration = data.get("Duration", 0)
        self.size = data.get("Size", 0)
        self.width = data.get("Width", 0)
        self.height = data.get("Height", 0)
        self.fps = data.get("FPS", 0)
        self.bit_rate = data.get("BitRate", 0)
        self.format = data.get("Format", "")
        self.download_url = data.get("DownLoadURL", "")
        self.failed_reason = data.get("FailedReason", "")
        self.status = data.get("Status", "")

        self.media_type = data.get("MediaType", "")
        self.media_tag = data.get("MediaTag", "")
        self.media_second_tag = data.get("MediaSecondTag", "")
        self.media_lang = data.get("MediaLang", "")


@retry(stop_max_attempt_number=3)
def post_http(header, url, req):
    print(req)
    response = requests.post(url=url, data=json.dumps(req), headers=header)
    if response.status_code != 200:
        return None, MediaResponse(
            {"RequestID": "", "Error": {"Code": str(response.status_code), "Message": "http failed"}})

    response_map = json.loads(response.text)
    print(response.text)
    return response_map, None


@retry(stop_max_attempt_number=3)
def get_http(header, url):
    response = requests.get(url=url, headers=header)
    if response.status_code != 200:
        return None, MediaResponse(
            {"RequestID": "", "Error": {"Code": str(response.status_code), "Message": "http failed"}})

    return response.content, None


def get_md5(s):
    md = hashlib.md5()
    md.update(s)
    return md.hexdigest()


class MediaAsset(object):
    def __init__(self, media_config):
        self.media_config = media_config
        self.url = "http://{}:{}/gateway".format(media_config.host, media_config.port)

    def __get_header__(self, action):
        ts = TiSign(self.media_config.host,
                    action,
                    self.media_config.version,
                    self.media_config.service,
                    'application/json',
                    'POST',
                    self.media_config.secret_id,
                    self.media_config.secret_key)

        http_header_dict, authorization = ts.build_header_with_signature()
        return http_header_dict, authorization

    # DownloadFile 通过媒体信息返回的url下载文件到本地
    def download_file(self, download_url, dir2, file_name):
        resp, err = self.download_t_buf(download_url)
        if err.code != "ok":
            return err

        if not os.path.exists(dir2):
            os.makedirs(dir2)

        with open("{}/{}".format(dir2, file_name), "wb") as f:
            f.write(resp)

        return MediaResponse({"RequestID": "", "Error": {"Code": "ok", "Message": "success"}})

    # download_t_buf 通过媒体信息返回的url下载文件到内存
    def download_t_buf(self, download_url):
        ts = TiSign(self.media_config.host,
                    "DownloadFile",
                    self.media_config.version,
                    self.media_config.service,
                    "application/octet-stream",
                    'GET',
                    self.media_config.secret_id,
                    self.media_config.secret_key)

        http_header_dict, authorization = ts.build_header_with_signature()
        url = "http://{}:{}{}".format(self.media_config.host, self.media_config.port, download_url)

        resp, err = get_http(http_header_dict, url)
        if err is not None:
            return None, err
        return resp, MediaResponse({"RequestID": "", "Error": {"Code": "ok", "Message": "success"}})

    # describe_medias 拉取媒体列表
    def describe_medias(self, page_number, page_size, filter_by):

        req = {
            "TIBusinessID": self.media_config.business,
            "TIProjectID": self.media_config.project,
            "PageNumber": page_number,
            "PageSize": page_size,
            "FilterBy": filter_by.to_map(),
            "Inner": False,
            "Action": "DescribeMedias"
        }

        http_header_dict, authorization = self.__get_header__("DescribeMedias")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is not None:
            return None, None, err

        response_err = MediaResponse(resp["Response"])
        if response_err.code != "ok":
            return None, None, response_err

        media_info = []
        for v in resp["Response"]["MediaInfoSet"]:
            media_info.append(MediaInfoSet(v))
        return media_info, resp["Response"]["TotalCount"], response_err

    # describe_media_details 获取指定媒体集的详情
    def describe_media_details(self, media_ids):
        req = {
            "TIBusinessID": self.media_config.business,
            "TIProjectID": self.media_config.project,
            "MediaIDSet": media_ids,
            "Action": "DescribeMediaDetails"
        }

        http_header_dict, authorization = self.__get_header__("DescribeMediaDetails")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is not None:
            return None, err

        response_err = MediaResponse(resp["Response"])
        if response_err.code != "ok":
            return None, response_err

        media_info = []
        for v in resp["Response"]["MediaInfoSet"]:
            media_info.append(MediaInfoSet(v))
        return media_info, response_err

    # remove_medias 删除指定媒体集
    def remove_medias(self, media_ids):
        req = {
            "TIBusinessID": self.media_config.business,
            "TIProjectID": self.media_config.project,
            "MediaIDSet": media_ids,
            "Action": "RemoveMedias"
        }

        http_header_dict, authorization = self.__get_header__("RemoveMedias")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is not None:
            return None, err

        response_err = MediaResponse(resp["Response"])
        if response_err.code != "ok":
            return None, response_err

        failed_media = []
        for v in resp["Response"]["FailedMediaSet"]:
            failed_media.append(FailedMediaInfo(v))
        return failed_media, response_err

    # describe_categories 返回可选媒体类型列表
    def describe_categories(self):
        req = {
            "TIBusinessID": self.media_config.business,
            "TIProjectID": self.media_config.project,
            "Action": "DescribeCategories"
        }

        http_header_dict, authorization = self.__get_header__("DescribeCategories")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is not None:
            return None, None, err

        response_err = MediaResponse(resp["Response"])
        if response_err.code != "ok":
            return None, None, response_err

        category = []
        lang = []
        label = []
        for v in resp["Response"]["CategorySet"]:
            category.append(Category(v))
        for v in resp["Response"]["LabelSet"]:
            label.append(Label(v))
        for v in resp["Response"]["LangSet"]:
            lang.append(v)
        return category, label, lang, response_err

    # modify_media 修改媒体信息
    def modify_media(self, media_id, media_tag, media_second_tag):
        req = {
            "TIBusinessID": self.media_config.business,
            "TIProjectID": self.media_config.project,
            "MediaID": media_id,
            "MediaTag": media_tag,
            "MediaSecondTag": media_second_tag,
            "Action": "ModifyMedia"
        }

        http_header_dict, authorization = self.__get_header__("ModifyMedia")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is None:
            return MediaResponse(resp["Response"])
        return err

    # modify_expire_time 修改文件过期时间，当前时间算起来，有效时间为 days 天
    def modify_expire_time(self, media_id, days):
        req = {
            "TIBusinessID": self.media_config.business,
            "TIProjectID": self.media_config.project,
            "MediaID": media_id,
            "Days": days,
            "Action": "ModifyExpireTime"
        }

        http_header_dict, authorization = self.__get_header__("ModifyExpireTime")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is None:
            return MediaResponse(resp["Response"])
        return err

    def apply_upload(self, media_name, media_meta, file_size):
        req = {
            "TIBusinessID": self.media_config.business,
            "TIProjectID": self.media_config.project,
            "Name": media_name,
            "MediaMeta": media_meta.to_map(),
            "Size": str(file_size),
            "Inner": False,
            "Action": "ApplyUpload"
        }
        block_Size = 32 * 1024 * 1024
        if file_size < block_Size:
            req["UsePutObject"] = 1
        http_header_dict, authorization = self.__get_header__("ApplyUpload")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is not None:
            return None, err

        response_err = MediaResponse(resp["Response"])
        if response_err.code != "ok":
            return None, response_err

        return resp["Response"], response_err

    def do_upload(self, file_path, file_size, media_msg):

        block_Size = 32 * 1024 * 1024
        number = int(file_size / block_Size) + 1

        coroutine_num = 4
        if number < coroutine_num:
            coroutine_num = number

        req_list = []
        f = open(file_path, "rb")

        if file_size < block_Size:
            ts = TiSign(self.media_config.host,
              "PutObject",
              self.media_config.version,
              self.media_config.service,
              "application/octet-stream",
              'PUT',
              self.media_config.secret_id,
              self.media_config.secret_key)
            filebuf = f.read()
            query = "useJson=true&Bucket={}&Key={}&Content-MD5={}".format(
                        media_msg["Bucket"], media_msg["Key"], get_md5(filebuf))
            url = "http://{}:{}/FileManager/PutObject?{}".format(self.media_config.host, self.media_config.port,
                                                                          query)
            http_header_dict, authorization = ts.build_header_with_signature()
            
            try_times = 5
            sleep_time = 0.05
            while try_times > 0:
                response_err = MediaResponse({"RequestID": "", "Error": {"Code": "ok", "Message": ""}})
                resp = requests.put(url=url, headers=http_header_dict, data=filebuf)
                if resp.status_code == 200:
                    dic = json.loads(resp.text)
                    response_err = MediaResponse(dic["Response"])
                    if response_err.code == "ok":
                        return response_err
                    else:
                        response_err = MediaResponse({"RequestID": "", "Error": {"Code": response_err.code, "Message": resp.text}})
                else:
                    response_err = MediaResponse({"RequestID": "", "Error": {"Code": "http put failed", "Message": resp.status}})
                try_times -= 1
                time.sleep(sleep_time)
                sleep_time *= 2
                
            return response_err
        else:
            ts = TiSign(self.media_config.host,
              "UploadPart",
              self.media_config.version,
              self.media_config.service,
              "application/octet-stream",
              'PUT',
              self.media_config.secret_id,
              self.media_config.secret_key)
            for i in range(number):
                http_header_dict, authorization = ts.build_header_with_signature()
                if i + 1 == number:
                    data = f.read(file_size % block_Size)
                    query = "useJson=true&Bucket={}&Key={}&uploadId={}&partNumber={}&Content-MD5={}".format(
                        media_msg["Bucket"], media_msg["Key"], media_msg["UploadId"], i + 1, get_md5(data))
                    url = "http://{}:{}/FileManager/UploadPart?{}".format(self.media_config.host, self.media_config.port,
                                                                          query)
                    req_list.append(grequests.put(url=url, headers=http_header_dict, data=data))
                elif (i + 1) % coroutine_num == 0:
                    data = f.read(block_Size)
                    query = "useJson=true&Bucket={}&Key={}&uploadId={}&partNumber={}&Content-MD5={}".format(
                        media_msg["Bucket"], media_msg["Key"], media_msg["UploadId"], i + 1, get_md5(data))
                    url = "http://{}:{}/FileManager/UploadPart?{}".format(self.media_config.host, self.media_config.port,
                                                                          query)
                    req_list.append(grequests.put(url=url, headers=http_header_dict, data=data))
                else:
                    data = f.read(block_Size)
                    query = "useJson=true&Bucket={}&Key={}&uploadId={}&partNumber={}&Content-MD5={}".format(
                        media_msg["Bucket"], media_msg["Key"], media_msg["UploadId"], i + 1, get_md5(data))
                    url = "http://{}:{}/FileManager/UploadPart?{}".format(self.media_config.host, self.media_config.port,
                                                                          query)

                    req_list.append(grequests.put(url=url, headers=http_header_dict, data=data))
                    continue
                try_times = 5
                sleep_time = 0.05
                while try_times > 0:
                    res_list = grequests.map(req_list)
                    new_req_list = []
                    new_res_list = []
                    for i in range(len(req_list)):
                        if res_list[i].status_code != 200:
                          new_req_list.append(req_list[i])
                          new_res_list.append(res_list[i])
                        else:
                          dic = json.loads(res_list[i].text)
                          response_err = MediaResponse(dic["Response"])
                          if response_err.code != "ok":
                            new_req_list.append(req_list[i])
                            new_res_list.append(res_list[i])
                    req_list = new_req_list
                    res_list = new_res_list
                    if len(req_list) == 0:
                      break
                    try_times -= 1
                    time.sleep(sleep_time)
                    sleep_time *= 2

                if len(req_list) != 0:
                  if res_list[0].status_code != 200:
                    dic = json.loads(res_list[0].text)
                    return MediaResponse(dic["Response"])
                  else:
                    return MediaResponse({"RequestID": "", "Error": {"Code": "http put failed", "Message": res_list[0].status}})
        return MediaResponse({"RequestID": "", "Error": {"Code": "ok", "Message": "http failed"}})

    def commit_upload(self, media_msg):
        req = {
            "TIBusinessID": self.media_config.business,
            "TIProjectID": self.media_config.project,
            "MediaID": media_msg["MediaID"],
            "Bucket": media_msg["Bucket"],
            "Key": media_msg["Key"],
            "UploadId": media_msg["UploadId"],
            "Action": "CommitUpload"
        }

        http_header_dict, authorization = self.__get_header__("CommitUpload")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is None:
            return MediaResponse(resp["Response"])
        return err

    # upload_medias array of UploadMedia
    def create_medias(self, upload_medias):
        req = {
            "TIBusinessID": self.media_config.business,
            "TIProjectID": self.media_config.project,
            "UploadMediaSet": [media.to_map() for media in upload_medias]
        }

        http_header_dict, authorization = self.__get_header__("CreateMedias")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is None:
            media_infos = []
            for v in resp["Response"]["UploadMediaInfoSet"]:
                media_infos.append(UploadMediaInfo(v))
            return media_infos, MediaResponse(resp["Response"])
        return None, err
    
    # upload_file 通过媒体信息返回的url下载文件到本地
    def upload_file(self, file_path, media_name, media_meta):

        if not os.path.exists(file_path):
            return None, MediaResponse(
                {"RequestID": "", "Error": {"Code": "failed", "Message": "file path is failed."}})

        file_size = os.path.getsize(file_path)

        media_msg, err = self.apply_upload(media_name, media_meta, file_size)
        if err.code != "ok":
            return None, err

        err = self.do_upload(file_path, file_size, media_msg)
        if err.code != "ok":
            return None, err

        err = self.commit_upload(media_msg)
        if err.code != "ok":
            return None, err

        media_info, err = self.describe_media_details([media_msg["MediaID"]])
        if err.code != "ok":
            return None, err

        return media_info[0], err

    # check_status_failed 检查媒体状态是否失败
    @staticmethod 
    def check_status_failed(state):
      return state == MediaState.FAILED.value or state == MediaState.DELETED.value or \
        state == MediaState.CLEANED.value
    
    # check_status_success 检查媒体状态是否成功
    @staticmethod
    def check_status_success(state):
      return state == MediaState.COMPLETED.value