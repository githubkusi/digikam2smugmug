from iso8601 import parse_date


class Image(object):
    def __init__(self, image):
        self.uri = image["Uri"]
        self.title = image["Title"]
        self.caption = image["Caption"]
        self.keywords = image["Keywords"]
        self.filename = image["FileName"]
        self.archived_size = image["ArchivedSize"]
        self.image_key = image["ImageKey"]
        self.last_updated = parse_date(image["LastUpdated"]).replace(tzinfo=None)

    @classmethod
    def from_album_image(cls, image):
        image["Uri"] = image["Uris"]["Image"]
        return cls(image)

    @classmethod
    def get_image(cls, connection, image_uri):
        response, code = connection.get(image_uri)
        assert code == 200
        return cls(response["Image"])

    def delete_image(self, connection):
        return connection.delete(self.uri)

    def change_image(self, connection, changes):
        '''
        :param connection:
        :param dict changes: example {"Keyword" : "Snow"}
        :return:
        '''
        return Image(connection.patch(self.uri, changes)["Response"]["Image"])

    def set_keywords(self, connection, keywords):
        d = {"KeywordArray": keywords}
        return self.change_image(connection, d)
