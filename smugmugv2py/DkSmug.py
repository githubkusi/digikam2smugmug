from os import path
import os
import glob
from .Album import Album
from .AlbumImage import AlbumImage
from .Node import Node


class DkSmug:
    def __init__(self):
        self.bla = 'hello'

    @staticmethod
    def get_or_create_node_from_folder_path(connection, node, folder_path):
        # if url_path in cache.keys():
        #     return node.get_node(cache[url_path])

        folder_names = folder_path.strip(os.sep).split(os.sep)

        for folder_name in folder_names:
            child_node = node.find_node_by_name(connection, folder_name)
            if child_node is None:
                # Folder does not exist, create new
                print("create folder " + folder_name)
                node = node.create_child_folder(connection, folder_name, None, 'Private')
            else:
                # Folder exists, use child node
                print("use existing folder " + folder_name)
                node = child_node

        return node

    @staticmethod
    def get_or_create_album_from_album_name(connection, node_uri, album_name):
        node = Node.get_node(connection, node_uri)
        album_node = node.find_node_by_name(connection, album_name)
        if album_node is None:
            print("create album " + album_name + " in folder " + node.url_path)
            album_node = node.create_child_album(connection, name=album_name, url=None, privacy='Private')

        return Album.get_album(connection, album_node.album_uri)

    def get_or_create_album_from_album_path(self, connection, node, album_path):
        folder_path, album_name = path.split(album_path)
        if folder_path == os.sep:
            # no folder, album is attached at the root node
            folder_node = node
        else:
            folder_node = self.get_or_create_node_from_folder_path(connection, node, folder_path)

        return self.get_or_create_album_from_album_name(connection, folder_node.uri, album_name)

    @staticmethod
    def folder_contains_media_files(root_path, folder_path):
        extensions = ['*.jpg', '*.JPG', '*.mov', '*.MOV', '*.mp4', '*.wmv', '*.WMV']
        for ext in extensions:
            p = path.join(root_path, folder_path.strip(os.sep), ext)
            if glob.glob(p).__len__() > 0:
                return True

        return False

    @staticmethod
    def get_album_image_uri_from_name(image_name, connection, album_node):
        album_images = album_node.get_album_images(connection)
        for album_image in album_images:
            if image_name == album_image.filename:
                return album_image.uri

        return None

    def upload_image(self, connection, root_node, file_path, album_url_path):
        album_node = self.get_or_create_album_from_album_path(connection, root_node, album_url_path)
        # album = Album.get_album(connection, album)
        return connection.upload_image(file_path, album_node.uri)

    @staticmethod
    def get_keywords(dk, cursor, image_id):
        keywords = dk.get_tags(cursor, image_id)
        rating = dk.get_rating(cursor, image_id)
        album_name = dk.get_album_name(cursor, image_id)

        keywords.append("Star{}".format(rating))
        keywords.append(album_name)
        return keywords

    def sync_tags(self, dk, cursor, conn_dk, connection):
        dk_image_ids = dk.get_synched_image_ids(cursor)
        # dk_image_ids = [667587]
        for dk_image_id in dk_image_ids:
            mtime_tags_local = dk.get_local_tags_mtime(cursor, dk_image_id)
            mtime_remote = dk.get_remote_tags_mtime(cursor, dk_image_id)
            mtime_rating_local = dk.get_local_rating_mtime(cursor, dk_image_id)

            has_outdated_tags = mtime_tags_local is not None and mtime_tags_local > mtime_remote
            has_outdated_rating = mtime_rating_local is not None and mtime_rating_local > mtime_remote

            if has_outdated_tags or has_outdated_rating:
                keywords = self.get_keywords(dk, cursor, dk_image_id)
                album_image_uri = dk.get_remote_id(cursor, dk_image_id)
                album_image = AlbumImage.get_album_image(connection, album_image_uri)
                image = album_image.get_image(connection)
                print("set keywords on " + image.filename, keywords)
                image.set_keywords(connection, keywords)
                dk.update_mtime_tags(conn_dk, cursor, dk_image_id)
