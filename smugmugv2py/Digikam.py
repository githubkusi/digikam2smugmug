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
    def get_unsynced_image_ids(cursor):
        query = """
        SELECT Images.Id
        FROM Images
        LEFT JOIN PhotoSharing ON PhotoSharing.imageid = Images.id
        WHERE PhotoSharing.imageid IS NULL
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        image_ids = [x[0] for x in rows]
        return image_ids

    @staticmethod
    def get_synched_image_ids(cursor):
        query = "SELECT imageid FROM PhotoSharing"
        cursor.execute(query)
        rows = cursor.fetchall()
        image_ids = [x[0] for x in rows]
        return image_ids

    @staticmethod
    def get_tags(cursor, image_id):
        query = """
        select t1.name
        from Tags t1
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {} and t1.id > 20
        union all
        select t2.name
        from Tags t1
        left join Tags t2 on t2.id=t1.pid
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {} and t2.id > 20
        union all
        select t3.name
        from Tags t1
        left join Tags t2 on t2.id=t1.pid
        left join Tags t3 on t3.id=t2.pid
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {} and t3.id > 20
        union all
        select t4.name
        from Tags t1
        left join Tags t2 on t2.id=t1.pid
        left join Tags t3 on t3.id=t2.pid
        left join Tags t4 on t4.id=t3.pid
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {} and t4.id > 20
        """.format(image_id, image_id, image_id, image_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        keywords = [x[0] for x in rows]  # (('blue',), ('Lifesaver',))
        return keywords

    @staticmethod
    def get_remote_id(cursor, image_id):
        query = """
        select remoteid from PhotoSharing
        where imageid = {}
        """.format(image_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1
        remote_id = rows[0][0]
        return remote_id



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


