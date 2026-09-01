--liquibase formatted sql

--changeset diegopacheco:002-create-gin-index-jsonb-ops
CREATE INDEX idx_documents_data_gin ON documents USING gin (data);
--rollback DROP INDEX idx_documents_data_gin;

--changeset diegopacheco:003-create-gin-index-jsonb-path-ops
CREATE INDEX idx_documents_data_path_gin ON documents USING gin (data jsonb_path_ops);
--rollback DROP INDEX idx_documents_data_path_gin;
