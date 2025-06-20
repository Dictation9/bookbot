#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python email_handlers/send_full_report.py 