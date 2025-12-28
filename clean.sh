#!/usr/bin/env bash

find . -type f \( -name "*.pyc" -o -name ".DS_Store" \) -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
