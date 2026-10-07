#!/bin/bash
export PYTHONPATH=.
python3 -m pytest backend/tests/ > test_out.txt 2>&1
echo "Pytest exit code: $?" >> test_out.txt
python3 evaluation/evaluate.py --limit 3 > eval_out.txt 2>&1
echo "Eval exit code: $?" >> eval_out.txt
