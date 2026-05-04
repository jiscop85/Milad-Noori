"""اجرای کامل پروژه – از شبیه‌سازی تا گزارش نهایی"""

import sys
import logging
from datetime import datetime
import numpy as np
import pandas as pd

from src.config import SimParams, Paths
from src.orbit import SatelliteOrbit
from src.telemetry import TelemetrySimulator
from src.processor import DataProcessor
from src.visualizer import Visualizer

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_simulation(duration_hours: float = None, interval_sec: int = None):
    logger.info("شروع فرآیند صفر تا صد داده‌پرداز ماهواره‌ای")
    
    # 1. تنظیمات
    params = SimParams()
    if duration_hours:
        params.duration_hours = duration_hours
    if interval_sec:
        params.interval_sec = interval_sec
    
    # 2. تعریف مدار (مدار LEO نمونه)
    epoch = params.start_time
    orbit = SatelliteOrbit(
        a_km=6971.0, e=0.001, i_deg=51.6, raan0_deg=120.0,
        argp0_deg=0.0, M0_deg=0.0, epoch=epoch
    )
    logger.info(f"مدار تعریف شد: نیم‌قطر بزرگ {orbit.a} km، انحراف {np.degrees(orbit.i):.1f}°")
    
    # 3. شبیه‌سازی تله‌متری
    logger.info("تولید داده‌های تله‌متری ...")
    sim = TelemetrySimulator(orbit, params)
    df = sim.generate()
    logger.info(f"تعداد رکوردها: {len(df)}")
    
    # 4. پردازش و ناهنجاری‌یابی
    numeric_cols = ['temp_C', 'voltage_V', 'current_A', 'signal_dBm', 'fuel_flow_kgps']
    df = DataProcessor.flag_all_anomalies(df, numeric_cols)
    stats = DataProcessor.compute_statistics(df, numeric_cols)
    report = DataProcessor.generate_anomaly_report(df)
    
    # 5. ذخیره فایل CSV
    csv_path = Paths.data_dir / f"telemetry_{epoch.strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"داده‌های خام در {csv_path} ذخیره شد")
    
    # 6. ذخیره گزارش متنی
    report_path = Paths.output_dir / "anomaly_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report + "\n\n")
        f.write("آمار توصیفی:\n")
        f.write(stats.to_string())
    logger.info(f"گزارش ناهنجاری در {report_path} ذخیره شد")
    
    # 7. مصورسازی
    Visualizer.plot_telemetry(df)
    Visualizer.plot_ground_track(df)
    
    # 8. نمایش خلاصه در کنسول
    print("\n" + "="*60)
    print(report)
    print("\nآمار سریع (میانگین آخری):")
    print(stats.loc[['mean', 'std', '50%', '99%']])
    print("="*60)
    logger.info("پروژه با موفقیت به پایان رسید. هیچ توقفی رخ نداد.")
    
if __name__ == "__main__":
    # پشتیبانی از آرگومان خط فرمان: python -m src.main --duration 4 --interval 60
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, help="مدت شبیه‌سازی (ساعت)")
    parser.add_argument("--interval", type=int, help="فاصله نمونه‌برداری (ثانیه)")
    args = parser.parse_args()
    run_simulation(duration_hours=args.duration, interval_sec=args.interval)