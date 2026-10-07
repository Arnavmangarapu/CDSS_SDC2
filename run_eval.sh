#!/bin/bash
export PYTHONPATH=.
python3 evaluation/evaluate.py --limit 1 > eval_out.txt 2>&1
echo "Exit: $?" >> eval_out.txt
