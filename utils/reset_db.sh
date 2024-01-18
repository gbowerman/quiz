#!/bin/bash

# this script truncates data but does not delete database
sudo -i -u postgres psql -d quiz_db < ../sql/reset_schema.sql
