#!/usr/bin/env bash

# Install system dependencies for WeasyPrint PDF generation
apt-get update && apt-get install -y libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Install Python dependencies
pip install -r requirements.txt
