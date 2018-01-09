from os import path
from .Album import Album
from .Node import Node

class DkSmug:
    def __init__(self):
        self.bla = 'hello'

    @staticmethod
    def get_or_create_node_from_folder_path(connection, node, url_path):
        # if url_path in cache.keys():
        #     return node.get_node(cache[url_path])

        print(url_path)
        s = url_path.split('/')
        folder_names = s[1:]

        for folder_name in folder_names:
            child_node = node.find_node_by_url_name(connection, folder_name)
            if child_node is None:
                # Folder does not exist, create new
                node = node.create_child_folder(connection, folder_name, folder_name, 'Private')
            else:
                # Folder exists, use child node
                node = child_node

        return node

    @staticmethod
    def get_or_create_album_from_album_name(connection, node_uri, url_name):
        '''
        :param connection:
        :param node:
        :param url_name: /Testfolder/SubfolderUrl/AlbumUrl
        :return:
        '''
        node = Node.get_node(connection, node_uri)
        album_node = node.find_node_by_url_name(connection, url_name)
        if album_node is None:
            album_node = node.create_child_album(connection, url_name, url_name, 'Private')

        return Album.get_album(connection, album_node.album_uri)

    def get_or_create_album_from_album_path(self, connection, node, url_path):
        folder_path, album_name = path.split(url_path)
        if folder_path == '/':
            # no folder, album is attached at the root node
            folder_node = node
        else:
            folder_node = self.get_or_create_node_from_folder_path(connection, node, folder_path)

        return self.get_or_create_album_from_album_name(connection, folder_node.uri, album_name)

    # @staticmethod
    # def image_exists(image_id, connection):

    def upload_image(self, connection, root_node, file_path, album_url_path):
        album_node = self.get_or_create_album_from_album_path(connection, root_node, album_url_path)
        # album = Album.get_album(connection, album)
        return connection.upload_image(file_path, album_node.uri)


