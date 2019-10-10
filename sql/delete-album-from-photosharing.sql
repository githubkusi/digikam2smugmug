select * from PhotoSharing
where imageid in (
select i.id from Images i
inner join Albums a on i.album = a.id
inner join PhotoSharing p on p.imageid = i.id
where relativePath like '%20140801 Island' )



delete from PhotoSharing
where imageid in (
select i.id from Images i
inner join Albums a on i.album = a.id
inner join PhotoSharing p on p.imageid = i.id
where relativePath like '%20140801 Island' )