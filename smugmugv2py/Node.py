from json import dumps
from pprint import pprint


class Node(object):
    '''
    FOLDER
    NodeID:  VmPBjP
    Uri:     /api/v2/node/VmPBjP
    Name:    testfolder
    UrlName: Testfolder
    UrlPath: /Testfolder
    WebUri:  http://photos.leuthold.org/Testfolder/n-VmPBjP
    Type:    Folder

    SUBFOLDER
    NodeID:  gQ5JpD
    Uri:     /api/v2/node/gQ5JpD
    Name:    Subfolder
    UrlName: SubfolderUrl
    UrlPath: /Testfolder/SubfolderUrl
    WebUri:  http://photos.leuthold.org/Testfolder/SubfolderUrl/n-gQ5JpD
    Type:    Folder

    ALBUM IN SUBFOLDER (AS NODE)
    NodeID:  gQCKtt
    Uri:     /api/v2/node/gQCKtt
    Name:    Album
    UrlName: AlbumUrl
    UrlPath: /Testfolder/SubfolderUrl/AlbumUrl
    WebUri:  http://photos.leuthold.org/Testfolder/SubfolderUrl/AlbumUrl/n-gQCKtt
    Type:    Album

    SAME ALBUM IN SUBFOLDER (AS ALBUM)
    NodeID:  gQCKtt
    Uri:     /api/v2/album/7fVP8m
    Name:    Album
    UrlName: AlbumUrl
    UrlPath: /Testfolder/SubfolderUrl/AlbumUrl
    WebUri:  http://photos.leuthold.org/Testfolder/SubfolderUrl/AlbumUrl/n-gQCKtt

    ALBUMIMAGE IN ALBUM (COLLECTED)
    Uri:       /api/v2/album/7fVP8m/image/KnjKc5p-0
    ImageKey:  KnjKc5p
    FileName:  IMG_2167.JPG
    WebUri:    http://photos.leuthold.org/Testfolder/SubfolderUrl/AlbumUrl/n-gQCKtt/i-KnjKc5p

    IMAGE IN ORIGINAL ALBUM
    Uri:         /api/v2/image/KnjKc5p-0
    ArchivedUri: https://photos.smugmug.com/17h10-Flumserberg/i-KnjKc5p/0/14ab3392/D/IMG_2167-D.jpg
    WebUri:      http://photos.leuthold.org/17h10-Flumserberg/i-KnjKc5p
    '''
    def __init__(self, node):
        self.uri = node["Uri"]
        self.description = node["Description"]
        self.name = node["Name"]
        self.url_name = node["UrlName"]
        self.url_path = node["UrlPath"]
        self.type = node["Type"]
        self.privacy = node["Privacy"]
        self.has_children = node["HasChildren"]

        if self.type == "Album" or self.type == "System Album":
            self.sort_method = node["SortMethod"]
            self.sort_direction = node["SortDirection"]
            if "Uri" in node["Uris"]["Album"]:
                self.album_uri = node["Uris"]["Album"]["Uri"]
            else:
                self.album_uri = node["Uris"]["Album"]
        elif self.type == "Folder":
            self.sort_method = node["SortMethod"]
            self.sort_direction = node["SortDirection"]
            if "Uri" in node["Uris"]["ChildNodes"]:
                self.__child_nodes = node["Uris"]["ChildNodes"]["Uri"]
            else:
                self.__child_nodes = node["Uris"]["ChildNodes"]

    @classmethod
    def get_node(cls, connection, node_uri):
        response, code = connection.get(node_uri)
        return cls(response["Node"])

    def has_children_online(self, connection):
        response, code = connection.get(self.uri)
        hc = response["Node"]["HasChildren"]
        return hc

    def get_children(self, connection):
        ret = []

        if self.has_children_online(connection):
            response, code = connection.get(self.__child_nodes)
            if 'Node' in response:
                nodes = response["Node"]
                for node in nodes:
                    this_node = Node(node)
                    ret.append(this_node)

        return ret

    def __create_child_node(self, connection, type, name, url, privacy, description):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

        if url is None:
            params = {
                'Type': type,
                'Name': name,
                'Privacy': privacy,
            }
        else:
            params = {
                'Type': type,
                'Name': name,
                'UrlName': url,
                'Privacy': privacy,
            }

        if description:
            params['Description'] = description

        response = connection.post(self.__child_nodes, data=dumps(params), headers=headers)

        if response['Code'] is not 201:
            print("Error from SmugMug:\nCode: {}\nMessage: {}"
                  .format(response['Code'], response['Message']))

        return response['Response']

    def create_child_folder(self, connection, name, url, privacy, description=None):
        # url needs to start with a capital letter or number
        response = self.__create_child_node(connection, 'Folder', name, url, privacy, description)
        return Node(response["Node"])

    def create_child_album(self, connection, name, url, privacy, description=None):
        response = self.__create_child_node(connection, 'Album', name, url, privacy, description)
        return Node(response["Node"])

    def delete_node(self, connection):
        return connection.delete(self.uri)

    def change_node(self, connection, changes):
        return connection.patch(self.uri, changes)["Response"]["Node"]

    def find_node_by_url_name(self, connection, url_name):
        for node in self.get_children(connection):
            if node.url_name == url_name:
                return node

        return None

    def find_album_by_url_name(self, connection, url_name):
        for node in self.get_children(connection):
            if node.url_name == url_name:
                return node

    def find_node_by_name(self, connection, name):
        for node in self.get_children(connection):
            if node.name == name:
                return node

        return None

    def find_album_by_name(self, connection, name):
        for node in self.get_children(connection):
            if node.name == name:
                return node

        return None

    def find_all_albums(self, connection):
        albums = []
        for node in self.get_children(connection):
            if node.type == "Folder":
                print('enter ' + node.name)
                albums.extend(node.find_all_albums(connection))

            elif node.type == "Album":
                albums.append(node.album_uri)

        return albums

    def set_name(self, connection, new_name):
        return Node(self.change_node(connection, {"Name": new_name}))