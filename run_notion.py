name: Run Notion Script

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * *'

jobs:
  run:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: pip install notion-client==2.0.11
    
    - name: Run script
      env:
        NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
        NOTION_DB_ID: ${{ secrets.NOTION_DB_ID }}
      run: python run_notion.py
