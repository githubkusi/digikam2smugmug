import MySQLdb as Mdb
import os
from etaprogress.progress import ProgressBar
from functools import reduce


class Digikam:
    def __init__(self):
        self.bla = 'hello'

    @staticmethod
    def get_connection_and_cursor(user, passwd, db, host='localhost'):
        con = Mdb.connect(host, user, passwd, db, use_unicode=True, charset='utf8')

        cursor = con.cursor()
        return con, cursor

    @staticmethod
    def get_album_url_path_and_image_name_and_rating(cursor, image_id):
        query = """
        select
            Albums.relativePath,
            Images.name,
            ImageInformation.rating
        from
            Images
        INNER JOIN ImageInformation ON
            ImageInformation.imageid = Images.id 
        inner join Albums ON
            Albums.id = Images.album
        where
            Images.id = {}
        """.format(image_id)

        cursor.execute(query)
        res = cursor.fetchone()
        if res is None:
            return None, None, None
        return res

    @staticmethod
    def get_album_name(cursor, image_id):
        """
        :param cursor:
        :param image_id:
        :return: folder name, e.g. '20180208 Fasnacht'
        """
        query = """
        select Albums.relativePath from Images, Albums 
        where Images.id = {} and 
        Albums.id = Images.album 
        """.format(image_id)

        cursor.execute(query)
        res = cursor.fetchone()
        assert res is not None
        return os.path.basename(res[0])

    @staticmethod
    def get_image_name(cursor, image_id):
        """
        :param cursor:
        :param image_id:
        :return: image name, e.g. 'image.jpg'
        """
        query = f"""
        select name from Images 
        where id = {image_id} 
        """

        cursor.execute(query)
        res = cursor.fetchone()
        assert res is not None
        return os.path.basename(res[0])

    @staticmethod
    def get_image_path(cursor, image_id):
        """
        :param cursor:
        :param image_id:
        :return: image path, e.g. '/2018/20180208 event/img.jpg'
        """
        query = f"""
        select Albums.relativePath, Images.name from Images, Albums 
        where Images.id = {image_id} and 
        Albums.id = Images.album 
        """
        cursor.execute(query)
        res = cursor.fetchone()
        assert res is not None
        return res[0] + os.path.sep + res[1]

    @staticmethod
    def get_unsynced_image_ids(cursor):
        # Get images from Digikam which don't have a corresponding entry in PhotoSharing.imageid
        # This includes images which will later be filtered due to rating/tags/etc...
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
                    Tags.name = "SmugmugNoSync"
            )
        """
        # AND ImageInformation.creationDate > '2017-10-01 15:00:00'
        cursor.execute(query)
        rows = cursor.fetchall()
        image_ids = [x[0] for x in rows]
        return image_ids

    @staticmethod
    def get_synched_image_ids(cursor):
        # query = "SELECT imageid FROM PhotoSharing"
        query = """
                SELECT imageid FROM PhotoSharing p
                INNER JOIN Images i ON i.id = p.imageid
                WHERE i.album is not NULL
                """
        # query = """
        #         SELECT p.imageid FROM PhotoSharing p
        #         INNER JOIN ImageInformation i ON i.imageid = p.imageid
        #         WHERE i.creationDate > '2018-01-01 15:00:00'
        #         """
        cursor.execute(query)
        rows = cursor.fetchall()
        image_ids = [x[0] for x in rows]
        return image_ids

    def get_outdated_image_ids(self, cursor):
        unsynched_image_ids = []
        image_ids = self.get_synched_image_ids(cursor)
        # image_ids = [667587]

        num_images = image_ids.__len__()
        bar = ProgressBar(num_images)

        for image_id in image_ids:
            # progress bar
            bar.numerator = bar.numerator + 1
            print(bar, end='\r', flush=True)

            mtime_metadata_remote = self.get_remote_metadata_mtime(cursor, image_id)

            # tag timestamps
            # ImageTags.mtime gets updated on changing the caption/title
            # Therefore has_outdated_tags is of limited use
            mtime_tags_local = self.get_local_tags_mtime(cursor, image_id)
            has_outdated_tags = mtime_tags_local is not None and mtime_tags_local > mtime_metadata_remote

            # rating timestamp, local rating is a remote tag, hence a mtime_rating_remote is not needed
            mtime_rating_local = self.get_local_rating_mtime(cursor, image_id)
            has_outdated_rating = mtime_rating_local is not None and mtime_rating_local > mtime_metadata_remote

            # comment (title/caption) timestamp
            mtime_comments_local = self.get_local_comments_mtime(cursor, image_id)
            has_outdated_comments = mtime_comments_local is not None and mtime_comments_local > mtime_metadata_remote

            if has_outdated_tags or has_outdated_rating or has_outdated_comments:
                s = ""
                if has_outdated_tags:
                    s += "tags,"
                if has_outdated_rating:
                    s += "rating,"
                if has_outdated_comments:
                    s += "comments,"

                if num_images < 1000:
                    print(f"outdated {s[:-1]} on {self.get_image_name(cursor, image_id)}")
                unsynched_image_ids.append(image_id)

        bar.numerator = num_images
        print(bar)

        return unsynched_image_ids

    @staticmethod
    def get_internal_tagid(cursor):
        query = "select id from Tags where name = \"_Digikam_Internal_Tags_\""
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1, "mysql: internal dk tag not found"
        return rows[0][0]

    @staticmethod
    def get_tags(cursor, image_id):
        """
        :param cursor:
        :param image_id:
        :return: tags as list of str
        """
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

        # Query for tags including parent tags
        query = """
        select t1.name
        from Tags t1
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {image} and t1.pid <> {internal_tag} and t1.id <> {internal_tag} and t1.id <> {root_tag}
        union all
        select t2.name
        from Tags t1
        left join Tags t2 on t2.id=t1.pid
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {image} and t2.pid <> {internal_tag} and t2.id <> {internal_tag} and t2.id <> {root_tag}
        union all
        select t3.name
        from Tags t1
        left join Tags t2 on t2.id=t1.pid
        left join Tags t3 on t3.id=t2.pid
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {image} and t3.pid <> {internal_tag} and t3.id <> {internal_tag} and t3.id <> {root_tag}
        union all
        select t4.name
        from Tags t1
        left join Tags t2 on t2.id=t1.pid
        left join Tags t3 on t3.id=t2.pid
        left join Tags t4 on t4.id=t3.pid
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {image} and t4.pid <> {internal_tag} and t4.id <> {internal_tag} and t4.id <> {root_tag}
        """.format(image=image_id, internal_tag=iid, root_tag=rid)

        # Query for tags without parent tags
        query = """
        select t1.name
        from Tags t1
        inner join ImageTags on ImageTags.tagid = t1.id
        where ImageTags.imageid = {image} and t1.pid <> {internal_tag} and t1.id <> {internal_tag} and t1.id <> {root_tag}        
        """.format(image=image_id, internal_tag=iid, root_tag=rid)
        cursor.execute(query)
        rows = cursor.fetchall()
        keywords = [x[0] for x in rows]  # (('blue',), ('Lifesaver',))
        return keywords

    @staticmethod
    def get_rating(cursor, image_id):
        query = """
                select rating from ImageInformation
                where imageid = {}
                """.format(image_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        count = rows.__len__()
        assert count <= 1
        if count == 1:
            return rows[0][0]
        elif count == 0:
            # not yet rated, treat as 0
            return 0
        else:
            raise ValueError('{} ratings found for image_id {}'.format(count, image_id))

    @staticmethod
    def get_title(cursor, image_id):
        query = """
                SELECT comment FROM ImageComments
                WHERE imageid = {} and type = 3
                """.format(image_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        count = rows.__len__()
        if count > 0:
            assert count == 1
            return rows[0][0]
        else:
            return None

    def get_caption(self, cursor, image_id):
        query = f"""
                SELECT comment FROM ImageComments
                WHERE imageid = {image_id} and type = 1
                """
        cursor.execute(query)
        rows = cursor.fetchall()
        count = rows.__len__()
        if count == 1:
            return rows[0][0]
        elif count > 1:
            image_path = self.get_image_path(cursor, image_id)
            if reduce(lambda a, b: a if a == b else None, rows) is None:
                Exception("{count} non-identical captions found for image {image_path}")
            else:
                print(f"{count} identical captions found for image {image_path}, use the first")
                return rows[0][0]

        else:
            return None

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
    def update_metadata_mtime(conn_dk, cursor, image_id):
        query = """
            UPDATE PhotoSharing SET mtime_metadata = CURRENT_TIMESTAMP
            WHERE imageid = {}
            """.format(image_id)
        cursor.execute(query)
        conn_dk.commit()

    def get_local_tags_mtime(self, cursor, image_id):
        """
        :param cursor:
        :param image_id:
        :return: get youngest timestamp of all tags
        """
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
    def get_local_rating_mtime(cursor, image_id):
        """
        :param cursor:
        :param image_id:
        :return: get timestamp of rating
        """
        query = """
                SELECT mtime FROM ImageInformation
                WHERE imageid = {}
                """.format(image_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1
        return rows[0][0]

    @staticmethod
    def get_remote_metadata_mtime(cursor, image_id):
        """
        :param cursor:
        :param image_id:
        :return: datetime.datetime(year, month, day, hour, min, sec)
        """
        query = """
                SELECT mtime_metadata FROM PhotoSharing
                WHERE imageid = {}
                """.format(image_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1
        return rows[0][0]

    @staticmethod
    def get_local_comments_mtime(cursor, image_id):
        """
        :param cursor:
        :param image_id:
        :return: get timestamp of title
        """
        query = """
                SELECT mtime FROM ImageComments
                WHERE imageid = {} and type in (1, 3)
                """.format(image_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        mtimes = [i[0] for i in rows]
        if mtimes.__len__() == 0:
            return None
        else:
            return max(mtimes)


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
    def is_image_in_photosharing(cursor, remote_id):
        query = """
                SELECT imageid FROM PhotoSharing
                WHERE remoteid = "{}";
                """.format(remote_id)
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows.__len__() > 0

    @staticmethod
    def get_root_path(cursor):
        query = """
                SELECT type, identifier FROM AlbumRoots
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        assert rows.__len__() == 1, "Only one album root supported but you have {}".format(rows.__len__())
        assert rows[0][0] == 3, "Only network shares are supported"
        identifier = rows[0][1]
        return identifier.split("networkshareid:?mountpath=", 1)[1]

    @staticmethod
    def delete_from_photosharing(cursor):
        query = """
                DELETE from PhotoSharing
                FROM imageid in (
                SELECT i.id from Images i
                inner join Albums a on i.album = a.id
                inner join PhotoSharing p on p.imageid = i.id
                where relativePath like '%20140801 Island' )
                """

