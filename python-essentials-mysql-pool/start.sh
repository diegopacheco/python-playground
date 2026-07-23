#!/bin/bash

podman-compose up -d

until podman exec python-essentials-mysql-pool_mysql_1 mysqladmin ping -h 127.0.0.1 -uroot -proot --silent >/dev/null 2>&1; do
  sleep 1
done
echo "mysql ready"