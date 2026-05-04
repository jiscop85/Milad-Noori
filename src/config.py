"""تنظیمات مرکزی پروژه - مسیرها، ثابت‌های فیزیکی و پارامترهای پیش‌فرض"""

import os
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Physics:
    """ثابت‌های فیزیکی و مداری"""
    GM_EARTH: float = 398600.4418      # km^3/s^2
    R_EARTH: float = 6371.0             # km
    OMEGA_EARTH: float = 7.292115e-5    # rad/s
    J2: float = 1.08262668e-3           # ضریب تخت شدن زمین

@dataclass(frozen=True)
class Paths:
    """مسیرهای پوشه‌های ورودی/خروجی"""
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir: str = os.path.join(base_dir, "data")
    output_dir: str = os.path.join(base_dir, "outputs")
    
    def __post_init__(self):
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

@dataclass(frozen=True)
class SimParams:
    """پارامترهای شبیه‌سازی"""
    start_time: datetime = datetime(2025, 6, 1, 0, 0, 0)
    duration_hours: float = 6.0
    interval_sec: int = 30
    anomaly_prob: float = 0.015         # احتمال تزریق ناهنجاری