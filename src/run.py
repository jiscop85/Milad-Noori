#!/usr/bin/env python3
"""
اسکریپت اجرای سریع پروژه SatVision
"""

from src.main import run_simulation

if __name__ == "__main__":
    # می‌توانید مقادیر پیش‌فرض را در اینجا تغییر دهید
    run_simulation(duration_hours=6, interval_sec=30)