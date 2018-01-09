#!/usr/bin/python3

#nodeid: 67btMX

from smugmugv2py import Connection, User, Node, Album, AlbumImage, Image, SmugMugv2Exception
from sys import stdout, stdin
from os import linesep, path
from pprint import pprint
from test_setup import api_key, api_secret, token, secret
from datetime import datetime
from json import dumps
from requests import exceptions
from smugmugv2py import Digikam, DkSmug
import os


def do_indent(indent):
    for x in range(0, indent):
        stdout.write(" ")


def print_album(node, indent):
    album = Album.get_album(connection, node.album_uri)
    stdout.write(", " + str(album.image_count) + " images")
    images = album.get_images(connection)
    for image in images:
        do_indent(indent + 1)
        print(image.filename + " - " + image.caption)


def print_node(node, indent):
    do_indent(indent)
    stdout.write("'" + node.name + "' (" + node.type + ") - " + node.privacy)
    if node.type == "Album":
        print_album(node, indent)
    print()
    children = node.get_children(connection)
    for child in children:
        print_node(child, indent + 1)


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


def get_image_uris(images):
    image_uris = []
    for image in images:
        image_uris.append(image.uri)

    return image_uris


def get_all_image_uris(conn, node):
    image_uris = []
    for child_node in node.get_children(conn):
        if child_node.type == "Album":
            album = Album.get_album(conn, child_node.album_uri)
            images = album.get_images(conn)
            image_uris = image_uris + get_image_uris(images)

    return image_uris


def get_some_image_uris(conn, node):
    image_uris = []
    for child_node in node.get_children(conn):
        if child_node.type == "Album":
            album = Album.get_album(conn, child_node.album_uri)
            images = album.get_images(conn)
            image_uris = image_uris + get_image_uris(images)
            return image_uris


def set_keywords(connection, uri, keywords):
    kw = {"KeywordArray": keywords}
    connection.patch(uri, kw)["Response"]["Image"]


def upload_image(conn, root_node, filename, album_name):
    album = root_node.find_node(album_name)
    conn.upload_image(filename, album.uri)


def get_node(connection, root_node, name):

    for node in root_node.get_children(connection):
        if node.url_name == name:
            return node

    raise ValueError(name + ' not found')


def get_digikam_node(connection):
    root_node = get_root_node(connection)
    return get_node(connection, root_node, 'Digikam')


def get_album_uri_from_url_path(connection, root_node, url_path):
    for node in root_node.get_children(connection):
        print(node.url_path)
        if node.type == "Folder":
            album_uri = get_album_uri_from_url_path(connection, node, url_path)
            if album_uri is not None:
                return album_uri

        if node.type == "Album":
            if node.url_path == url_path:
                return node.album_uri

    return None


def get_album_node_from_url_path(connection, root_node, url_path):
    # extract first folder
    folder, album = os.path.split(url_path)


def get_folder_node_from_url_path(connection, url_path, root_node):
    for node in root_node.get_children(connection):
        if node.type == "Folder":
            found_node = get_folder_node_from_url_path(connection, url_path, node)
            if found_node.url_path == url_path:
                return found_node
    return None


def main():
    connection = get_authorized_connection(api_key, api_secret, token, secret)
    dk_node = get_digikam_node(connection)

    conn_dk, cursor = Digikam.get_connection_and_cursor(
        user='dkuser',
        passwd='dkpasswd',
        db='digikam_devel_core')

    # connection.get_code('/api/v2/image/rvNZsjK')

    images_id = Digikam.get_unsynced_image_id(cursor)

    # Node.get_node(connection, '/api/v2/node/gQ5JpD')

    root_path = '/tmp/digikam-debug-pics'
    dks = DkSmug()
    for image_id in images_id:
        album_url_path, image_name = Digikam.get_album_url_path_and_image_name(cursor, image_id)
        file_path = os.path.join(root_path + album_url_path, image_name)
        album_node = dks.get_or_create_album_from_album_path(connection, dk_node, album_url_path)

        album_images = album_node.get_album_images(connection)
        file_names = [album_image.filename for album_image in album_images]

        if image_name in file_names:
            print("{} already in album {}, skipping".format(image_name, album_node.name))

        else:
            print("upload image {} to album {}".format(image_name, album_node.name))
            response = connection.upload_image(file_path, album_node.uri)
            Digikam.add_image_to_photosharing(conn_dk, cursor, image_id, response["Image"]["AlbumImageUri"])


    #
    # for image_id in images_id:
    #     album_url_path, image_name = Digikam.get_url_path(cursor, image_id)
    #     album_uri = get_album_uri_from_url_path(connection, dk_node, album_url_path)
    #     # if album_uri is None:
    #
    #
    #
    # # node_tf = get_node(connection, node, 'Testfolder')
    # # node_ta = get_node(connection, node_tf, 'Testalbum')
    # # connection.upload_image('adhawkins_github_avatar.jpg', node_ta.uri)
    #
    # album_uri = get_album_uri_from_url_path(connection, root_node, "/Testfolder/Hidden")
    #
    # image_uris = get_some_image_uris(connection, node)
    # print(image_uris)
    #
    # a = Image.get_image(connection, image_uris[0])
    # keywords = ['kw1', 'kw2']
    # b = a.set_keywords(connection, keywords)
    #
    #
    # print(b)


if __name__ == "__main__":
    main()