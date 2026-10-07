#!/bin/bash
export PYTHONPATH=.
python3 -m pytest backend/tests/ > test_out.txt 2>&1
echo "Exit: $?" >> test_out.txt
