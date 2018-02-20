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
        res = cursor.fetchone()
        if res is None:
            return None, None
        return res

    @staticmethod
    def get_unsynced_image_ids(cursor):
        query = """
        SELECT
            Images.id
        FROM
            Images
        LEFT JOIN PhotoSharing ON
            PhotoSharing.imageid = Images.id
        INNER JOIN ImageInformation ON
            ImageInformation.imageid = Images.id
        WHERE
            PhotoSharing.imageid IS NULL
            and ImageInformation.rating >= 1
            AND UPPER(ImageInformation.format) in ('MOV', 'MPEG', 'AVI', 'WMV', 'GIF', 'PNG', 'JPG', 'MP4')                        
            AND Images.status = 1
            AND Images.id not in(
                SELECT
                    Images.id
                FROM
                    Images
                INNER JOIN ImageTags ON
                    ImageTags.imageid = Images.id
                INNER JOIN Tags ON
                    Tags.id = ImageTags.tagid
                WHERE
                    Tags.name = "nosync"
            )
        """
        # AND ImageInformation.creationDate > '2017-10-01 15:00:00'
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
    def get_internal_tagid(cursor):
        query = "select id from Tags where name = \"_Digikam_Internal_Tags_\""
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1, "mysql: internal dk tag not found"
        return rows[0][0]

    @staticmethod
    def get_tags(cursor, image_id):
        query = "select id from Tags where name = \"_Digikam_Internal_Tags_\""
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1, "mysql: internal dk tag not found"
        iid = rows[0][0]

        query = "select id from Tags where name = \"_Digikam_root_tag_\""
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1, "mysql: root dk tag not found"
        rid = rows[0][0]

        query = """
        select t1.name
        from Tags t1
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {} and t1.pid <> {} and t1.id <> {} and t1.id <> {}
        union all
        select t2.name
        from Tags t1
        left join Tags t2 on t2.id=t1.pid
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {} and t2.pid <> {} and t2.id <> {} and t2.id <> {}
        union all
        select t3.name
        from Tags t1
        left join Tags t2 on t2.id=t1.pid
        left join Tags t3 on t3.id=t2.pid
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {} and t3.pid <> {} and t3.id <> {} and t3.id <> {}
        union all
        select t4.name
        from Tags t1
        left join Tags t2 on t2.id=t1.pid
        left join Tags t3 on t3.id=t2.pid
        left join Tags t4 on t4.id=t3.pid
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {} and t4.pid <> {} and t4.id <> {} and t4.id <> {}
        """.format(image_id, iid, iid, rid, image_id, iid, iid, rid, image_id, iid, iid, rid, image_id, iid, iid, rid)
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

    @staticmethod
    def update_mtime_tags(conn_dk, cursor, image_id):
        query = """
            UPDATE PhotoSharing SET mtime_tags = CURRENT_TIMESTAMP
            WHERE imageid = {}
            """.format(image_id)
        cursor.execute(query)
        conn_dk.commit()

    def get_local_tags_mtime(self, cursor, image_id):
        '''
        :param cursor:
        :param image_id:
        :return: get youngest timestamp of all tags
        '''
        internal_id = self.get_internal_tagid(cursor)

        query = """
                SELECT max(mtime) FROM ImageTags
                INNER JOIN Tags on Tags.id = ImageTags.tagid
                WHERE imageid = {} and Tags.pid <> {}
                """.format(image_id, internal_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1
        return rows[0][0]

    @staticmethod
    def get_remote_tags_mtime(cursor, image_id):
        query = """
                SELECT mtime_tags FROM PhotoSharing
                WHERE imageid = {}
                """.format(image_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1
        return rows[0][0]

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

    @staticmethod
    def is_image_in_photosharing(conn_dk, cursor, remote_id):
        query = """
                SELECT imageid FROM PhotoSharing
                WHERE remoteid = "{}";
                """.format(remote_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows.__len__() > 0


