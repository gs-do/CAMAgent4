#!/bin/bash

# Install chainlit with all dependencies
pip install --upgrade chainlit

# Try to fix missing frontend by reinstalling
pip uninstall -y chainlit
pip install chainlit --no-cache-dir

# Start the application
python -m chainlit run app.py --host 0.0.0.0 --port 8000