#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : utils/tools/url_tool.py

from urllib.parse import urljoin

import requests


def get_url_redirect_target(resp: requests.Response) -> str:
    if not resp.is_redirect:
        return resp.url

    location = resp.headers['Location']
    if not location:
        raise ValueError("Redirect response is missing a Location header.")

    return urljoin(resp.url, location)

