#!/usr/bin/python3

from rauth import OAuth1Service, OAuth1Session
from urllib.parse import urlsplit, urlunsplit, parse_qsl
from urllib.parse import urlencode
from json import loads, dumps
import requests
from os import path
from mimetypes import guess_type
from pkg_resources import get_distribution
import smugmugv2py


class Connection(object):
    BASE_URL = '/api/v2'
    UPLOAD_URL = 'https://upload.smugmug.com/'

    __OAUTH_ORIGIN = 'https://secure.smugmug.com'
    __REQUEST_TOKEN_URL = __OAUTH_ORIGIN + '/services/oauth/1.0a/getRequestToken'
    __ACCESS_TOKEN_URL = __OAUTH_ORIGIN + '/services/oauth/1.0a/getAccessToken'
    __AUTHORIZE_URL = __OAUTH_ORIGIN + '/services/oauth/1.0a/authorize'

    __API_ORIGIN = 'https://api.smugmug.com'

    __SERVICE = None
    __SESSION = requests.Session()

    def __init__(self, api_key, api_secret, user_agent=None):
        self.__user_agent = 'smugmugv2py/' + get_distribution('digikam2smugmug').version
        if user_agent:
            self.__user_agent += " - " + user_agent

        if self.__SERVICE is None:
            self.__SERVICE = OAuth1Service(
                name='smugmug-oauth-web-demo',
                consumer_key=api_key,
                consumer_secret=api_secret,
                request_token_url=self.__REQUEST_TOKEN_URL,
                access_token_url=self.__ACCESS_TOKEN_URL,
                authorize_url=self.__AUTHORIZE_URL,
                base_url=self.BASE_URL)

    @staticmethod
    def __add_auth_params(auth_url, access=None, permissions=None):
        if access is None and permissions is None:
            return auth_url
        parts = urlsplit(auth_url)
        query = parse_qsl(parts.query, True)
        if access is not None:
            query.append(('Access', access))
        if permissions is not None:
            query.append(('Permissions', permissions))
        return urlunsplit((
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query, True),
            parts.fragment))

    def get_auth_url(self, access=None, permissions=None):
        self.__rt, self.__rts = self.__SERVICE.get_request_token(params={'oauth_callback': 'oob'})

        auth_url = self.__add_auth_params(
            self.__SERVICE.get_authorize_url(self.__rt),
            access=access,
            permissions=permissions)

        return auth_url

    def get_access_token(self, verifier):
        at, ats = self.__SERVICE.get_access_token(self.__rt, self.__rts, params={'oauth_verifier': verifier})

        return at, ats

    def authorise_connection(self, token, token_secret):
        self.__SESSION = OAuth1Session(
            self.__SERVICE.consumer_key,
            self.__SERVICE.consumer_secret,
            access_token=token,
            access_token_secret=token_secret)

    def get(self, uri):
        attempt = 0
        while True:
            try:
                if attempt > 0:
                    print("Get, attempt: " + str(attempt))
                response = loads(self.__SESSION.get(
                    self.__API_ORIGIN + uri,
                    headers={
                        'Accept': 'application/json',
                        'User-Agent': self.__user_agent
                    },
                    params={
                        '_verbosity': '1',
                        'start': '1',
                        'count': '9999'
                    },
                    header_auth=True
                ).text)

                if "Response" in response:
                    return response["Response"], response["Code"]
                else:
                    raise smugmugv2py.SmugMugv2Exception(response["Message"])

            except requests.exceptions.RequestException as e:
                print("Caught exception " + str(e) + ", attempt: " + str(attempt))
                attempt += 1
                if attempt == 5:
                    raise

    def post(self, uri, headers=None, data=None):
        return self.raw_post(self.__API_ORIGIN + uri,
                             headers=headers,
                             data=data)

    def raw_post(self, uri, headers=None, data=None):
        headers['User-Agent'] = self.__user_agent

        request_models_response = self.__SESSION.post(
            uri,
            headers=headers,
            data=data,
            # params={'_verbosity': '1'},
            header_auth=True)

        content = request_models_response.content
        if not content:
            raise Exception(request_models_response)
        response = loads(content.decode("utf-8"))

        return response

    def delete(self, uri):
        headers = {
            'User-Agent': self.__user_agent,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        return loads(self.__SESSION.delete(
            self.__API_ORIGIN + uri,
            headers=headers,
            params={'_verbosity': '1'},
            data=None).content)

    def patch(self, uri, data):
        # example: connection.patch(album_uri, {"Share": true})
        headers = {
            'User-Agent': self.__user_agent,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        return loads(self.__SESSION.patch(
            self.__API_ORIGIN + uri,
            headers=headers,
            params={'_verbosity': '1'},
            data=dumps(data),
            header_auth=True).content.decode())

    def upload_image(self, filename, album_uri, caption=None, title=None, keywords=None):
        """
        :param filename:
        :param album_uri:
        :param caption:
        :param title:
        :param keywords:
        :return: response as dict
               "stat": "ok",
               "method": "smugmug.images.upload",
               "Image": {
                  "ImageUri": "/api/v2/album/<key>/image/<key>-0",
                  "AlbumImageUri": "/api/v2/album/<key>/image/<key>-0",
                  "StatusImageReplaceUri": null,
                  "URL": "http://example.smugmug.com/My-Gallery/i-<key>"
        """
        # x_smug_file_name = filename.encode('latin-1', 'ignore').decode()
        x_smug_file_name = filename
        headers = {
            'User-Agent': self.__user_agent,
            'X-Smug-ResponseType': 'JSON',
            'X-Smug-Version': 'v2',
            'Content-Type': guess_type(filename)[0],
            'X-Smug-AlbumUri': album_uri,
            'X-Smug-FileName': x_smug_file_name,
            'Content-Length': str(path.getsize(filename)),
        }

        if caption is not None:
            headers['X-Smug-Caption'] = caption

        if title is not None:
            headers['X-Smug-Title'] = title

        if keywords is not None:
            headers['X-Smug-Keywords'] = keywords

        with open(filename, "rb") as f:
            data = f.read()
            return self.raw_post(self.UPLOAD_URL, data=data, headers=headers)
