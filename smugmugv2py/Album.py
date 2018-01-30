from .AlbumImage import AlbumImage
from .Image import Image


class Album(object):
    def __init__(self, album):
        self.uri = album["Uri"]
        self.name = album["Name"]
        self.url_name = album["UrlName"]
        self.description = album["Description"]
        self.image_count = album["ImageCount"]
        self.keywords = album["Keywords"]
        self.sort_method = album["SortMethod"]
        self.sort_direction = album["SortDirection"]
        if self.image_count:
            self.__images = album["Uris"]["AlbumImages"]

    @classmethod
    def get_album(cls, connection, album_uri):
        response, code = connection.get(album_uri)
        return cls(response["Album"])

    def get_album_images(self, connection):
        ret = []

        if self.image_count:
            response, code = connection.get(self.__images)
            images = response["AlbumImage"]
            for image in images:
                this_image = AlbumImage(image)
                ret.append(this_image)

        return ret

    def get_images(self, connection):
        ret = []

        if self.image_count:
            response, code = connection.get(self.__images)
            album_images = response["AlbumImage"]
            for album_image in album_images:
                image = Image.from_album_image(album_image)
                ret.append(image)

        return ret

    def delete_album(self, connection):
        return connection.delete(self.uri)

    def change_album(self, connection, changes):
        return connection.patch(self.uri, changes)["Response"]["Album"]
