CREATE SCHEMA IF NOT EXISTS django_schema;
CREATE SCHEMA IF NOT EXISTS go_schema;
CREATE TABLE IF NOT EXISTS django_schema.records (
    id SERIAL PRIMARY KEY,
    number INTEGER NOT NULL,
    date DATE NOT NULL
);
CREATE TABLE IF NOT EXISTS go_schema.records (
    id SERIAL PRIMARY KEY,
    number INTEGER NOT NULL,
    date DATE NOT NULL
);
