#!/bin/bash
mysql -u user -p database -e "SELECT * FROM cameras" | tr '\t' ';' > cameras_oks.csv
