"""
Log Analysis Script for MAGGxDND
Analyzes recent logs and identifies issues
"""

import os
from datetime import datetime, timedelta
from pathlib import Path

LOG_DIR = Path('./logs')

def analyze_logs():
    print("="*60)
    print("MAGGxDND Log Analysis")
    print("="*60)
    print()
    
    # Check log directories
    log_categories = ['api', 'ai', 'database', 'game', 'websocket', 'errors']
    
    for category in log_categories:
        log_path = LOG_DIR / category
        if log_path.exists():
            files = list(log_path.glob('*.log'))
            print(f"✓ {category.upper()} logs: {len(files)} files")
            for f in files[:3]:  # Show first 3 files
                size = f.stat().st_size
                print(f"  - {f.name}: {size:,} bytes")
        else:
            print(f"✗ {category.upper()} logs: Directory not found")
    
    print()
    
    # Check for errors in API log
    api_log = LOG_DIR / 'api' / 'api.log'
    if api_log.exists():
        print("Analyzing API log...")
        error_count = 0
        warning_count = 0
        
        with open(api_log, 'r', encoding='utf-8') as f:
            for line in f:
                if 'ERROR' in line or '500' in line:
                    error_count += 1
                if 'WARNING' in line or '404' in line:
                    warning_count += 1
        
        print(f"  Errors (500): {error_count}")
        print(f"  Warnings (404): {warning_count}")
    
    print()
    print("="*60)
    print("Analysis Complete!")
    print("="*60)

if __name__ == '__main__':
    analyze_logs()
