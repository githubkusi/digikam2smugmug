from os import path
import os
import glob
import re
from .Album import Album
from .AlbumImage import AlbumImage
from .Node import Node
from .Image import Image
from etaprogress.progress import ProgressBar


class DkSmug:
    def __init__(self):
        self.bla = 'hello'

    @staticmethod
    def shorten_date(album_url_path):
        # convert 20180701 to 18-07
        return re.sub(
            r'[12]\d(\d\d)(\d\d)\d\d ',
            r'\1-\2 ',
            album_url_path)

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
                # print("use existing folder " + folder_name)
                node = child_node

        return node

    @staticmethod
    def get_or_create_album_from_album_name(connection, node_uri, album_name):
        node = Node.get_node(connection, node_uri)

        # shorten album name such that it's better visible on a smart phone. Keep full date for url
        # e.g 20180701 to 18-07 for smugmug
        album_name_shortened = DkSmug.shorten_date(album_name)

        album_node = node.find_node_by_name(connection, album_name_shortened)
        if album_node is None:
            print("create album " + album_name_shortened + " in folder " + node.url_path)
            album_node = node.create_child_album(connection, name=album_name, url=None, privacy='Unlisted')
            album_node = album_node.set_name(connection, album_name_shortened)

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

    @staticmethod
    def upload_image(connection, file_path, album_node_uri, title, caption, keywords):
        """
        :param connection:  smugmugv2py.Connection obj
        :param file_path:
        :param album_node_uri:
        :param title:
        :param caption:  str (can be multi-line)
        :param keywords: list of str
        :return: album_image_uri
        """

        if title is not None and title.__contains__("\n"):
            print(f'Warning: {file_path} contains multiple lines, squash them into one line')
            print(title)
            title = title.replace('\n', ' - ')

        keywords_str = '; '.join(keywords)
        response = connection.upload_image(file_path, album_node_uri, title=title, keywords=keywords_str)
        assert response['stat'] == 'ok', response['message']
        album_image_uri = response["Image"]["AlbumImageUri"]

        if caption is not None:
            # Do caption separately since caption in the header via X-Smug-Caption doesn't
            # support multi-line comments
            connection.patch(album_image_uri, {"Caption": caption})

        return album_image_uri

    @staticmethod
    def get_keywords(dk, cursor, image_id):
        keywords = dk.get_tags(cursor, image_id)
        rating = dk.get_rating(cursor, image_id)
        album_name = dk.get_album_name(cursor, image_id)

        # For an image with 3 stars, add Star1/2/3
        for i in range(1, rating + 1):
            keywords.append("Star{}".format(i))

        # Check for encoding issues
        assert album_name.find('\u0308') < 0, 'umlaut consists of a and ¨ instead of a single ä'

        keywords.append(album_name)
        return keywords

    def sync_metadata(self, dk, cursor, conn_dk, connection, exclude_tags):
        print("Find images with outdated metadata on Smugmug, according to PhotoSharing table")
        dk_image_ids = dk.get_outdated_image_ids(cursor)
        if dk_image_ids.__len__() == 0:
            print("All metadata on Smugmug are up-to-date")
            return

        num_images = dk_image_ids.__len__()
        bar = ProgressBar(num_images)

        print("Sync missing metadata")
        for dk_image_id in dk_image_ids:
            # progress bar
            bar.numerator = bar.numerator + 1
            if num_images > 1000:
                print(bar, end='\r', flush=True)
            else:
                print(bar)

            keywords = self.get_keywords(dk, cursor, dk_image_id)

            # breaks ordering
            if bool(exclude_tags):
                keywords = list(set(keywords) - exclude_tags)

            keywords_str = '; '.join(keywords)

            title = dk.get_title(cursor, dk_image_id)
            caption = dk.get_caption(cursor, dk_image_id)

            album_image_uri = dk.get_remote_id(cursor, dk_image_id)
            # album_image = AlbumImage.get_album_image(connection, album_image_uri)
            # image_uri = album_image.image_uri
            a = album_image_uri.split('/')
            image_uri = '/api/v2/image/' + a[-1]

            image_name = dk.get_image_name(cursor, dk_image_id)
            if num_images < 1000:
                print(f"set keywords={keywords_str}, title={title}, caption={caption} on {image_name}")
            connection.patch(image_uri, {"KeywordArray": keywords_str, "Title": title, "Caption": caption})

            dk.update_metadata_mtime(conn_dk, cursor, dk_image_id)