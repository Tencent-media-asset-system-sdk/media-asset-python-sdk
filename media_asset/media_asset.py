#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import json
import hashlib
import requests
import grequests
from retrying import retry

import sys

sys.path.append(".")
from .tisign.sign import *


class MediaResponse(object):
    def __init__(self, data):
        self.request_id = data["RequestID"]
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


class MediaInfoSet(object):
    def __init__(self, data):
        self.media_id = data["MediaID"]
        self.name = data["Name"]
        self.duration = data["Duration"]
        self.size = data["Size"]
        self.width = data["Width"]
        self.height = data["Height"]
        self.fps = data["FPS"]
        self.bit_rate = data["BitRate"]
        self.format = data["Format"]
        self.download_url = data["DownLoadURL"]
        self.failed_reason = data["FailedReason"]
        self.status = data["Status"]

        self.media_type = data["MediaType"]
        self.media_tag = data["MediaTag"]
        self.media_second_tag = data["MediaSecondTag"]
        self.media_lang = data["MediaLang"]


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
        for v in resp["Response"]["CategorySet"]:
            category.append(Category(v))
        label = []
        for v in resp["Response"]["LabelSet"]:
            label.append(Label(v))
        return category, label, response_err

    # modify_Media 修改媒体信息
    def modify_Media(self, media_id, media_tag, media_second_tag):
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

        http_header_dict, authorization = self.__get_header__("ApplyUpload")
        resp, err = post_http(http_header_dict, self.url, req)
        if err is not None:
            return None, err

        response_err = MediaResponse(resp["Response"])
        if response_err.code != "ok":
            return None, response_err

        return resp["Response"], response_err

    def do_upload(self, file_path, file_size, media_msg):
        ts = TiSign(self.media_config.host,
                    "UploadPart",
                    self.media_config.version,
                    self.media_config.service,
                    "application/octet-stream",
                    'PUT',
                    self.media_config.secret_id,
                    self.media_config.secret_key)

        http_header_dict, authorization = ts.build_header_with_signature()

        block_Size = 32 * 1024 * 1024
        number = int(file_size / block_Size) + 1

        coroutine_num = 8
        if number < coroutine_num:
            coroutine_num = number

        req_list = []
        f = open(file_path, "rb")
        for i in range(number):

            if i + 1 == number:
                data = f.read(file_size % block_Size)
                query = "useJson=true&Bucket={}&Key={}&uploadId={}&partNumber={}&Content-MD5={}".format(
                    media_msg["Bucket"], media_msg["Key"], media_msg["UploadId"], i + 1, get_md5(data))
                url = "http://{}:{}/FileManager/UploadPart?{}".format(self.media_config.host, self.media_config.port,
                                                                      query)
                req_list.append(grequests.put(url=url, headers=http_header_dict, data=data))
            elif i + 1 % coroutine_num == 0:
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

            res_list = grequests.map(req_list)
            for res in res_list:
                if res.status_code != 200:
                    return MediaResponse(
                        {"RequestID": "", "Error": {"Code": str(res.status_code), "Message": "http failed"}})
            req_list = []

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
