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

category, label, response_err = media_asset.describe_categories()
print(category[0].tag_set, label[0].second_tag_set, response_err.code)

media_meta = MediaMeta("视频", "新闻", "", "0")
media_info, response_err = media_asset.upload_file("./test-beijingninzao-6mins.mp4", "setup.py", media_meta)
print(response_err.code, media_info.download_url)

media_info, response_err = media_asset.describe_media_details([media_info.media_id])
print(response_err.code)

response_err = media_asset.download_file(
    "/DownloadFile?Key=upload%2F6a%2Fc7%2F9d9db4a3b952a9f9804913-kiQFl4dQTVdbjGTvaNC4s5ORFNoSkMP0&Token=c40a082bc3f3a9b7bd409a261fdfe0fe&IsTemp=false",
    "./", "test.map")
print(response_err.code)
