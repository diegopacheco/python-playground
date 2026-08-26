#!/bin/bash
set -e

query() {
    podman exec alembic_postgres psql -U alembic_user -d alembic_db -tAc "$1"
}

expect() {
    if [ "$2" != "$3" ]; then
        echo "FAIL: $1 expected '$3' got '$2'"
        exit 1
    fi
    echo "PASS: $1"
}

.venv/bin/alembic upgrade head

expect "teams table exists" "$(query "SELECT to_regclass('public.teams') IS NOT NULL")" "t"
expect "members table exists" "$(query "SELECT to_regclass('public.members') IS NOT NULL")" "t"
expect "members has team foreign key" "$(query "SELECT count(*) FROM information_schema.table_constraints WHERE table_name='members' AND constraint_type='FOREIGN KEY'")" "1"
expect "version is 0002" "$(query "SELECT version_num FROM alembic_version")" "0002"

.venv/bin/alembic downgrade 0001
expect "downgrade drops members" "$(query "SELECT to_regclass('public.members') IS NULL")" "t"
expect "downgrade keeps teams" "$(query "SELECT to_regclass('public.teams') IS NOT NULL")" "t"

.venv/bin/alembic upgrade head
expect "re-upgrade restores members" "$(query "SELECT to_regclass('public.members') IS NOT NULL")" "t"

echo "all tests passed"
