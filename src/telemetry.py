"""شبیه‌سازی داده تله‌متری چندحسگری با روندهای فیزیکی و ناهنجاری قابل تزریق"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from src.orbit import SatelliteOrbit
from src.config import SimParams, Physics

class TelemetrySimulator:
    def __init__(self, orbit: SatelliteOrbit, params: SimParams):
        self.orbit = orbit
        self.params = params
        # ساختن بردار زمان (ثانیه از مبدأ)
        self.t_seconds = np.arange(0, params.duration_hours*3600, params.interval_sec)
        self.timestamps = [params.start_time + timedelta(seconds=s) for s in self.t_seconds]
        
    def _add_realistic_trends(self, t_seconds: np.ndarray) -> dict:
        """تولید روند پایه برای هر حسگر (بدون نویز و ناهنجاری)"""
        orbit_num = t_seconds / 5400.0   # هر 90 دقیقه یک دور
        # دما (وابسته به نور خورشید)
        temp_base = 15 + 12 * np.sin(2*np.pi*orbit_num / 2)
        # ولتاژ باتری (واپاشی تدریجی)
        voltage_base = 28.2 - 0.05 * (t_seconds / 3600) + 0.3*np.sin(2*np.pi*orbit_num/3)
        # جریان بار
        current_base = 4.5 + 1.2*np.sin(2*np.pi*orbit_num/1.8)
        # قدرت سیگنال
        signal_base = -65 - 5*np.sin(2*np.pi*orbit_num/2)
        # دبی سوخت (کاهش خطی)
        fuel_flow_base = 0.12 - 1e-6 * t_seconds
        # تابش (وابسته به عرض جغرافیایی)
        lat, _ = self.orbit.get_lat_lon(t_seconds)
        radiation_base = 0.2 + 0.15 * np.abs(np.sin(np.radians(lat)))
        # وضعیت ADCS (دوران ماهواره فرضی)
        adcs_rate_base = 0.05 + 0.02*np.sin(2*np.pi*orbit_num/4)
        
        return {
            'temp': temp_base, 'volt': voltage_base, 'curr': current_base,
            'signal': signal_base, 'fuel_flow': fuel_flow_base,
            'radiation': radiation_base, 'adcs_rate': adcs_rate_base
        }
    
    def generate(self) -> pd.DataFrame:
        """ایجاد دیتافریم نهایی تله‌متری با نویز و ناهنجاری تصادفی"""
        t_sec = self.t_seconds
        trends = self._add_realistic_trends(t_sec)
        lat_arr, lon_arr = self.orbit.get_lat_lon(t_sec)
        
        # افزودن نویز گاوسی
        noise_scale = {
            'temp': 0.4, 'volt': 0.07, 'curr': 0.1, 'signal': 1.2,
            'fuel_flow': 0.005, 'radiation': 0.02, 'adcs_rate': 0.01
        }
        data = {}
        for key, base in trends.items():
            data[key] = base + np.random.normal(0, noise_scale[key], len(t_sec))
        
        # تزریق ناهنجاری بر اساس احتمال
        anomaly_mask = np.random.rand(len(t_sec)) < self.params.anomaly_prob
        for i in np.where(anomaly_mask)[0]:
            # انتخاب تصادفی نوع ناهنجاری
            anomaly_type = np.random.choice(['temp_spike', 'volt_drop', 'signal_loss', 'fuel_leak'])
            if anomaly_type == 'temp_spike':
                data['temp'][i] += np.random.choice([-18, 22])
            elif anomaly_type == 'volt_drop':
                data['volt'][i] -= np.random.uniform(2, 5)
            elif anomaly_type == 'signal_loss':
                data['signal'][i] -= np.random.uniform(15, 30)
            elif anomaly_type == 'fuel_leak':
                data['fuel_flow'][i] += np.random.uniform(0.05, 0.2)
        
        df = pd.DataFrame({
            'timestamp': self.timestamps,
            'lat_deg': lat_arr,
            'lon_deg': lon_arr,
            'temp_C': data['temp'],
            'voltage_V': data['volt'],
            'current_A': data['curr'],
            'signal_dBm': data['signal'],
            'fuel_flow_kgps': data['fuel_flow'],
            'radiation_wpm2': data['radiation'],
            'adcs_rate_dps': data['adcs_rate']
        })
        return df