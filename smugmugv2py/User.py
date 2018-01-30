from smugmugv2py import Connection


class User(object):
    def __init__(self, json):
        self.nickname = json["NickName"]
        self.name = json["Name"]
        self.node = json["Uris"]["Node"]

    @classmethod
    def get_authorized_user(cls, connection):
        response, code = connection.get(Connection.BASE_URL + '!authuser')
        return cls(response["User"])

    @classmethod
    def get_specific_user(cls, connection, user):
        response, code = connection.get(Connection.BASE_URL + "/user/" + user)
        return cls(response["User"])
