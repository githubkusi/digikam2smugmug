import MySQLdb as Mdb
import os

class Digikam:
    def __init__(self):
        self.bla = 'hello'

    @staticmethod
    def get_connection_and_cursor(user, passwd, db, host='localhost'):
        con = Mdb.connect(host, user, passwd, db)

        cursor = con.cursor()
        return con, cursor

    @staticmethod
    def get_album_url_path_and_image_name(cursor, image_id):
        query = """
        select Albums.relativePath, Images.name from Images, Albums 
        where Images.id = {} and 
        Albums.id = Images.album 
        """.format(image_id)
        cursor.execute(query)
        return cursor.fetchone()

    @staticmethod
    def get_unsynced_image_id(cursor):
        query = """
        SELECT Images.Id
        FROM Images
        LEFT JOIN PhotoSharing ON PhotoSharing.imageid = Images.id
        WHERE PhotoSharing.imageid IS NULL
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        images_id = [x[0] for x in rows]
        return images_id

    # @staticmethod
    # def get_root_path(self):
    #     query = """
    #             select Albums.relativePath, Images.name from Images, Albums
    #             where Images.id = %{:d} and
    #             Albums.id = Images.album
    #             """.format(image_id)
    #     cursor.execute(query)
    #     return cursor.fetchone()
    #

    @staticmethod
    def add_image_to_photosharing(conn_dk, cursor, image_id, remote_id):
        query = """
                INSERT INTO PhotoSharing (imageid,remoteid)
                VALUES ({},"{}");
                """.format(image_id, remote_id)
        cursor.execute(query)
        conn_dk.commit()
        return cursor.fetchone()


