# smugv2py
Python library for the SmugMug v2 API

# using

Install the freshest version

    pip install --update https://github.com/adhawkins/smugmugv2py/tarball/master

# want to help?

Install it in dev mode:

    python setup.py develop

# Python 3 caveats

You need to apply this PRQ https://github.com/litl/rauth/pull/201 to rauth in order to make rauth work with python3    


# Digikamdb

## New table PhotoSharing
- imageid:          Foreign Key to Images.ID (e.g 326490)
- remoteid:         SmugmugID (e.g /api/v2/album/dpgRrc/image/9SjdbR5-0)
- mtime\_metadata:  Timestamp of metadata on Smugmug. Currently, this includes rating, tags, title and caption

## Alter existing tables
- Add column mtime to ImageTags        : updated when tag is set (seemingly it is also updated on changing the rating)
- Add column mtime to ImageInformation : updated when rating is set
- Add column mtime to ImageComments    : updated when title or caption is set

## Convert stock digikam sql db
mysql -uYOURLOGIN -pYOURPASS <YOURDBNAME> < sql/create-photosharing.sql
mysql -uYOURLOGIN -pYOURPASS <YOURDBNAME> < sql/add-timestamp.sql




