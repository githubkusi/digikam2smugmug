#!/usr/bin/python3

# node id: 67btMX

from smugmugv2py import Connection, User, Node, Album, AlbumImage, Image, SmugMugv2Exception
from sys import stdout, stdin
from os import linesep, path
from pprint import pprint
from test_setup import api_key, api_secret, token, secret
from datetime import datetime
from json import dumps
from requests import exceptions
from smugmugv2py import Digikam, DkSmug
import time
from etaprogress.progress import ProgressBar
import os
import argparse
import configparser


def get_authorized_connection(api_key, api_secret, token, secret):
    if not api_key or not api_secret:
        raise Exception('API key and secret are required. see test_setup.py')

    connection = Connection(api_key, api_secret, user_agent="Test user agent/2.4")

    if not token or not secret:
        auth_url = connection.get_auth_url(access="Full", permissions="Modify")

        print("Visit the following URL and retrieve a verification code:%s%s" % (linesep, auth_url))

        stdout.write('Enter the six-digit code: ')
        stdout.flush()
        verifier = stdin.readline().strip()

        at, ats = connection.get_access_token(verifier)

        print("Token: " + at)
        print("Secret: " + ats)

        token = at
        secret = ats

    connection.authorise_connection(token, secret)

    return connection


def get_root_node(conn):
    user = User.get_authorized_user(conn)
    print("User: " + user.nickname + " (" + user.name + ")")

    return Node.get_node(conn, user.node)


def get_node(connection, root_node, name):
    for node in root_node.get_children(connection):
        if node.url_name == name:
            return node

    raise ValueError(name + ' not found')


def get_digikam_node(connection, digikam_node):
    root_node = get_root_node(connection)
    return get_node(connection, root_node, digikam_node)


def parse_exclude_file(root_path):
    file_name = '.smugmug-exclude'
    file_path = os.path.join(root_path, file_name)

    if not os.path.exists(file_path):
        return None

    parser = configparser.ConfigParser(allow_no_value=True)
    parser.optionxform = lambda option: option
    parser.read(file_path)
    exclude_paths = {ep for ep in parser['exclude paths'].keys()}
    exclude_tags = {et for et in parser['exclude tags'].keys()}
    exclude_files_with_tags = {et for et in parser['exclude files with tags'].keys()}

    return exclude_paths, exclude_tags, exclude_files_with_tags


def parse_args():
    parser = argparse.ArgumentParser(description="Digikam-to-SmugMug Uploader")
    parser.add_argument('-u', '--user', dest='user', required=True)
    parser.add_argument('-p', '--password', dest='passwd', required=True)
    parser.add_argument('-d', '--database', dest='database', required=True)
    parser.add_argument('-r', '--digikamnode', dest='digikam_node', required=False, default='Digikam')
    args = parser.parse_args()

    return args.user, args.passwd, args.database, args.digikam_node


def shorten_album_name():
    # rename albums
    # mynode = Node.get_node(connection, '/api/v2/node/3Xgpkt')
    albums = dk_node.find_all_albums(connection)
    for album_uri in albums:
        album = Album.get_album(connection, album_uri)
        new_name = dks.shorten_date(album.name)
        if album.name == new_name:
            print('skipping ' + album.name)
            continue

        else:
            print('{} -> {}'.format(album.name, new_name))
            album.set_name(connection, new_name)

    return


def main():
    user, password, database, digikam_node = parse_args()

    connection = get_authorized_connection(api_key, api_secret, token, secret)
    dk_node = get_digikam_node(connection, digikam_node)

    dk = Digikam()
    dks = DkSmug()

    conn_dk, cursor = dk.get_connection_and_cursor(
        user, password, database)

    root_path = dk.get_root_path(cursor)

    exclude_paths, exclude_tags, exclude_files_with_tags = parse_exclude_file(root_path)

    # a = "/share/Fotilis/2012/20120728 Hochzeit Landschi/Presentations/Martine à l'ENSIM.mov"
    # a = "asdf'sddf.jpg"
    # connection.upload_image(a, '/api/v2/album/7fVP8m')

    dk_image_ids = Digikam.get_unsynced_image_ids(cursor)
    print("Found {} unsynced images".format(dk_image_ids.__len__()))

    bar = ProgressBar(dk_image_ids.__len__())

    for dk_image_id in dk_image_ids:
        # progress bar
        bar.numerator = bar.numerator + 1
        print(bar)

        album_url_path, image_name = dk.get_album_url_path_and_image_name(cursor, dk_image_id)

        # check if user wants to ignore this image
        ignore = False
        if exclude_paths is not None:
            for exclude_path in exclude_paths:
                if album_url_path.startswith(exclude_path):
                    ignore = True

            if ignore:
                print("user ignores " + album_url_path)
                continue

        keywords = dks.get_keywords(dk, cursor, dk_image_id)
        t = set(keywords).intersection(exclude_files_with_tags)
        if t:
            print("exclude image {} due to tag {}".format(image_name, t))
            continue

        if album_url_path is None:
            print("image id {} not found".format(dk_image_id))
            continue
        file_path = os.path.join(root_path + album_url_path, image_name)

        # check validity of structure
        parent_folder_path, album_name = path.split(album_url_path)

        if dks.folder_contains_media_files(root_path, parent_folder_path.strip(os.sep)):
            print("<{}>: <{}> is an invalid album since there are media files in <{}>"
                  .format(image_name, album_name, parent_folder_path))
            continue

        album_node = dks.get_or_create_album_from_album_path(connection, dk_node, album_url_path)
        album_image_uri = dks.get_album_image_uri_from_name(image_name, connection, album_node)

        image_is_remote = album_image_uri is not None
        remote_id_is_in_database = image_is_remote and Digikam.is_image_in_photosharing(
            cursor, album_image_uri)

        if not image_is_remote and not remote_id_is_in_database:
            # normal case: upload
            print("upload image {} to album {}".format(image_name, album_node.name))
            keywords_str = '; '.join(keywords)
            response = connection.upload_image(file_path, album_node.uri, keywords=keywords_str)
            assert response['stat'] == 'ok', response['message']
            Digikam.add_image_to_photosharing(conn_dk, cursor, dk_image_id, response["Image"]["AlbumImageUri"])

        elif image_is_remote and not remote_id_is_in_database:
            # Image is remote, but not in PhotoSharing(e.g if uploader
            # crashes after upload but before PhotoSharing insert or image
            # was uploaded outside uploader)
            print("{} already in remote album {}. Add to local database with remote key {}"
                  .format(image_name, album_node.name, album_image_uri))
            Digikam.add_image_to_photosharing(conn_dk, cursor, dk_image_id, album_image_uri)

        elif image_is_remote and remote_id_is_in_database:
            err = "requested image {} is already in remote album {} and local " \
                  "database, impossible".format(image_name, album_node.name)
            raise ValueError(err)

        elif not image_is_remote and remote_id_is_in_database:
            # overwrite what’s in PhotoSharing
            raise ValueError('tbd')

    dks.sync_tags(Digikam(), cursor, conn_dk, connection, exclude_tags)
    print('done')

if __name__ == "__main__":
    main()
