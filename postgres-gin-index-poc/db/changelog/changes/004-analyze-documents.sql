--liquibase formatted sql

--changeset diegopacheco:006-analyze-documents runInTransaction:false runAlways:true
ANALYZE documents;
--rollback SELECT 1;
