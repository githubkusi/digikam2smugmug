
# node id: 67btMX

from smugmugv2py import Connection, User, Node, Album, AlbumImage, Image, SmugMugv2Exception
from sys import stdout, stdin
from os import linesep, path
from pprint import pprint
from datetime import datetime
from json import dumps
from requests import exceptions
from smugmugv2py import Digikam, DkSmug
import time
from etaprogress.progress import ProgressBar
import os
import argparse
import configparser
import yaml


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


def parse_config_file(root_path):
    file_name = '.smugmug-config'
    file_path = os.path.join(root_path, file_name)

    if not os.path.exists(file_path):
        return {}, {}, {}, {}

    parser = configparser.ConfigParser(allow_no_value=True)
    parser.optionxform = lambda option: option
    parser.read(file_path)
    exclude_paths = {ep for ep in parser['exclude paths'].keys()}
    exclude_tags = {et for et in parser['exclude tags'].keys()}
    exclude_files_with_tags = {et for et in parser['exclude files with tags'].keys()}
    d = dict(parser['minimal rating'])
    minimal_rating = dict([k, int(v)] for k, v in d.items())

    return exclude_paths, exclude_tags, exclude_files_with_tags, minimal_rating


def parse_args():
    default_config_filename = os.path.expanduser("~") + os.sep + ".digikam2smugmug.yml"

    parser = argparse.ArgumentParser(description="Digikam-to-SmugMug Uploader")
    parser.add_argument('-u', '--user', dest='user', required=False, default=None)
    parser.add_argument('-p', '--password', dest='passwd', required=False, default=None)
    parser.add_argument('-d', '--database', dest='database', required=False, default=None)
    parser.add_argument('-r', '--digikamnode', dest='digikam_node', required=False, default=None)
    parser.add_argument('-c', '--config', dest='config', required=False, default=default_config_filename)
    args = parser.parse_args()

    return args.user, args.passwd, args.database, args.digikam_node, args.config


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


def filter_unsynced_images(dk_image_ids, minimal_rating, exclude_paths, dk, cursor):
    minimal_default_rating = minimal_rating.get("DEFAULT", 0)

    dk_filtered_image_ids = []

    num_images = dk_image_ids.__len__()
    bar = ProgressBar(num_images)

    print("Filter unsynced images according to .smugmug-config")
    for dk_image_id in dk_image_ids:
        # progress bar
        bar.numerator = bar.numerator + 1
        print(bar, end='\r', flush=True)

        # album_url_path = '/2012/20120101/Event'
        album_url_path, image_name, rating = dk.get_album_url_path_and_image_name_and_rating(cursor, dk_image_id)
        if album_url_path is None:
            # delete the following images
            # select * from Images WHERE images.album is NULL
            print(f'Warning! Image.id = {dk_image_id} is not part of an Album. Skipping')
            continue

        image_path = album_url_path + '/' + image_name

        # check if user wants to ignore this image
        ignore = False
        if bool(exclude_paths):
            for exclude_path in exclude_paths:
                if image_path.startswith(exclude_path):
                    ignore = True

            if ignore:
                # print("user ignores " + album_url_path)
                continue

        if rating is None or rating == -1:
            rating = 0

        # check if minimal rating is reached
        if minimal_rating.__contains__(album_url_path):
            if minimal_rating[album_url_path] > rating:
                # print("exclude image {} due to too low rating".format(image_name))
                continue
        elif minimal_default_rating > rating:
            # print("{} is below default rating".format(image_name))
            continue

        dk_filtered_image_ids.append(dk_image_id)

    print("")
    return dk_filtered_image_ids


def read_config_smugmug(config_filename):
    with open(config_filename, 'r') as file:
        config = yaml.safe_load(file)
        c = config["smugmug"]
        return c["api_key"], c["api_secret"], c["token"], c["secret"]


def read_config_digikam(config_filename):
    with open(config_filename, 'r') as file:
        config = yaml.safe_load(file)
        c = config["digikam"]
        return c["user"], c["password"], c["database"], c["digikamnode"]


def main():
    user, password, database, digikam_node, config = parse_args()
    if user is None or password is None or digikam_node is None:
        user_cfg, password_cfg, database_cfg, digikam_node_cfg = read_config_digikam(config)

    user = user or user_cfg
    password = password or password_cfg
    database = database or database_cfg
    digikam_node = digikam_node or digikam_node_cfg

    api_key, api_secret, token, secret = read_config_smugmug(config)

    connection = get_authorized_connection(api_key, api_secret, token, secret)
    dk_node = get_digikam_node(connection, digikam_node)

    dk = Digikam()
    dks = DkSmug()

    conn_dk, cursor = dk.get_connection_and_cursor(
        user, password, database)

    root_path = dk.get_root_path(cursor)

    exclude_paths, exclude_tags, exclude_files_with_tags, minimal_rating = parse_config_file(root_path)

    # a = "/share/Fotilis/2012/20120728 Hochzeit Landschi/Presentations/Martine à l'ENSIM.mov"
    # a = "asdf'sddf.jpg"
    # connection.upload_image(a, '/api/v2/album/7fVP8m')

    print("Find unsynced images")
    dk_image_ids = Digikam.get_unsynced_image_ids(cursor)
    print("Found {} unsynced images".format(dk_image_ids.__len__()))

    dk_filtered_image_ids = filter_unsynced_images(dk_image_ids, minimal_rating, exclude_paths, dk, cursor)

    bar = ProgressBar(dk_filtered_image_ids.__len__())

    if dk_filtered_image_ids:
        print("Start uploading images")

    else:
        print("No images to be uploaded")

    for dk_image_id in dk_filtered_image_ids:
        # progress bar
        bar.numerator = bar.numerator + 1
        print(bar)

        # album_url_path = '/2012/20120101/Event'
        album_url_path, image_name, rating = dk.get_album_url_path_and_image_name_and_rating(cursor, dk_image_id)

        keywords = dks.get_keywords(dk, cursor, dk_image_id)
        title = dk.get_title(cursor, dk_image_id)
        caption = dk.get_caption(cursor, dk_image_id)
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

            album_image_uri = dks.upload_image(connection, file_path, album_node.uri, title, caption, keywords)
            if album_image_uri is None:
                print(f'Failure in uploading {file_path}, skipping')
                continue

            Digikam.add_image_to_photosharing(conn_dk, cursor, dk_image_id, album_image_uri)

        elif image_is_remote and not remote_id_is_in_database:
            # Image is remote, but not in PhotoSharing(e.g if uploader
            # crashes after upload but before PhotoSharing insert or image
            # was uploaded outside uploader)
            print("{} already in remote album {}. Add to local database with remote key {}"
                  .format(image_name, album_node.name, album_image_uri))
            Digikam.add_image_to_photosharing(conn_dk, cursor, dk_image_id, album_image_uri)

        elif image_is_remote and remote_id_is_in_database:
            err = "requested image {} is already in remote album [{}] with image uri [{}] and local " \
                  "database with imageId [{}], impossible".format(image_name, album_image_uri, album_node.name, dk_image_id)
            raise ValueError(err)

        elif not image_is_remote and remote_id_is_in_database:
            # overwrite what’s in PhotoSharing
            raise ValueError('tbd')

    dks.sync_metadata(Digikam(), cursor, conn_dk, connection, exclude_tags)
    print('Done')


if __name__ == "__main__":
    main()
