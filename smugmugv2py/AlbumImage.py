from iso8601 import parse_date
from .Image import Image

# An AlbumImage only has methods OPTIONS, GET, DELETE
# An Image has methods OPTIONS, GET, PATCH, DELETE
# An AlbumImage cannot be used to make changes like setting keywords. You need the image for that


class AlbumImage(object):
    def __init__(self, image):
        # if "Image" in image["Uris"]:
        #     # image is endpoint AlbumImage
        #     self.uri = image["Uris"]["Image"]
        # else:
        #     # image is endpoint Image
        #     self.uri = image["Uri"]
        self.uri = image["Uri"]
        self.image_uri = image["Uris"]["Image"]
        self.album_uri = image["Uris"]["Album"]
        self.title = image["Title"]
        self.caption = image["Caption"]
        self.keywords = image["Keywords"]
        self.filename = image["FileName"]
        self.archived_size = image["ArchivedSize"]
        self.image_key = image["ImageKey"]
        self.last_updated = parse_date(image["LastUpdated"]).replace(tzinfo=None)

    @classmethod
    def get_album_image(cls, connection, album_image_uri):
        response, code = connection.get(album_image_uri)
        assert code == 200, "failed to get album-image {}, error code {}".format(album_image_uri, code)
        return cls(response["AlbumImage"])

    def delete_album_image(self, connection):
        return connection.delete(self.uri)

    def get_image(self, connection):
        # unneeded connection. since props of Image and AlbumImage are (almost) identical,
        # they could just be copied over
        return Image.get_image(connection, self.image_uri)

