"""مصورسازی حرفه‌ای روند تله‌متری و رد زمینی"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from src.config import Paths

class Visualizer:
    @staticmethod
    def plot_telemetry(df: pd.DataFrame, save_name="telemetry_trends.png"):
        fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharex=True)
        time_vals = df['timestamp']
        params = [
            ('temp_C', '°C', 'دما', 'red'),
            ('voltage_V', 'V', 'ولتاژ باتری', 'green'),
            ('current_A', 'A', 'جریان بار', 'blue'),
            ('signal_dBm', 'dBm', 'قدرت سیگنال', 'magenta'),
            ('fuel_flow_kgps', 'kg/s', 'دبی سوخت', 'orange')
        ]
        for ax, (col, unit, title, color) in zip(axes, params):
            ax.plot(time_vals, df[col], color=color, lw=1.5, label=title)
            # نقاط ناهنجاری را با علامت X مشخص کن
            if f'anomaly_{col}' in df:
                anom = df[df[f'anomaly_{col}']]
                ax.scatter(anom['timestamp'], anom[col], marker='x', color='black', s=30, label='ناهنجاری')
            ax.set_ylabel(f"{title} ({unit})")
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
        axes[-1].set_xlabel('زمان (UTC)')
        plt.suptitle('روند داده‌های تله‌متری ماهواره (ناهنجاری‌ها با × مشخص شده)', fontsize=14)
        plt.tight_layout()
        path = Paths.output_dir / save_name
        plt.savefig(path, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"✅ نمودار تله‌متری ذخیره شد: {path}")
    
    @staticmethod
    def plot_ground_track(df: pd.DataFrame, save_name="ground_track.png"):
        plt.figure(figsize=(12, 6))
        sc = plt.scatter(df['lon_deg'], df['lat_deg'], c=df['timestamp'].astype('int64'), 
                         cmap='plasma', s=5, alpha=0.7)
        plt.colorbar(sc, label='زمان (از مبدأ)')
        plt.xlabel('طول جغرافیایی (درجه)')
        plt.ylabel('عرض جغرافیایی (درجه)')
        plt.title('ردیاب زمینی ماهواره (مسیر یک روزه)')
        plt.grid(alpha=0.2)
        path = Paths.output_dir / save_name
        plt.savefig(path, dpi=200, bbox_inches='tight')
        plt.close()
        print(f"✅ نقشه رد زمینی ذخیره شد: {path}")