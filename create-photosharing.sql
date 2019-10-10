DROP TABLE IF EXISTS PhotoSharing;
CREATE TABLE PhotoSharing
(imageid INTEGER PRIMARY KEY,
    remoteid LONGTEXT,
    CONSTRAINT PhotoSharing_Images FOREIGN KEY (imageid) REFERENCES Images (id) ON DELETE CASCADE ON UPDATE CASCADE,
    mtime_tags TIMESTAMP, mtime_comments TIMESTAMP);
