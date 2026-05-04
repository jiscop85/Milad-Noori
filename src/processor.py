"""پردازش داده، آمار و آشکارسازی ناهنجاری با روش‌های ترکیبی"""

import pandas as pd
import numpy as np
from typing import List, Dict

class DataProcessor:
    @staticmethod
    def compute_statistics(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
        return df[cols].describe(percentiles=[.01, .05, .95, .99])
    
    @staticmethod
    def detect_anomalies_zscore(df: pd.DataFrame, col: str, threshold=3.5) -> pd.Series:
        """ناهنجاری بر اساس Z‑score (فاصله از میانگین بر حسب انحراف معیار)"""
        mean = df[col].mean()
        std = df[col].std()
        return np.abs((df[col] - mean) / std) > threshold
    
    @staticmethod
    def detect_anomalies_iqr(df: pd.DataFrame, col: str, mult=1.5) -> pd.Series:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        iqr = Q3 - Q1
        lower = Q1 - mult*iqr
        upper = Q3 + mult*iqr
        return (df[col] < lower) | (df[col] > upper)
    
    @staticmethod
    def detect_anomalies_moving_average(df: pd.DataFrame, col: str, window=10, sigma=3) -> pd.Series:
        """ناهنجاری با انحراف از میانگین متحرک (برای ناهنجاری‌های محلی)"""
        roll_mean = df[col].rolling(window=window, center=True).mean()
        roll_std = df[col].rolling(window=window, center=True).std()
        # در ابتدا و انتها ممکن است NaN وجود داشته باشد -> آن‌ها را نادیده می‌گیریم
        z = (df[col] - roll_mean) / roll_std
        return (np.abs(z) > sigma).fillna(False)
    
    @classmethod
    def flag_all_anomalies(cls, df: pd.DataFrame, numeric_cols: List[str]) -> pd.DataFrame:
        """ترکیب سه روش مختلف و ذخیره نوع ناهنجاری"""
        for col in numeric_cols:
            z_anom = cls.detect_anomalies_zscore(df, col)
            iqr_anom = cls.detect_anomalies_iqr(df, col)
            ma_anom = cls.detect_anomalies_moving_average(df, col, window=15)
            # رأی‌گیری: اگر دست‌کم دو روش تأیید کنند، ناهنجار در نظر گرفته شود
            combined = (z_anom.astype(int) + iqr_anom.astype(int) + ma_anom.astype(int)) >= 2
            df[f'anomaly_{col}'] = combined
        df['any_anomaly'] = df[[f'anomaly_{col}' for col in numeric_cols]].any(axis=1)
        df['anomaly_count'] = df[[f'anomaly_{col}' for col in numeric_cols]].sum(axis=1)
        return df
    
    @staticmethod
    def generate_anomaly_report(df: pd.DataFrame) -> str:
        total = len(df)
        any_anom = df['any_anomaly'].sum()
        lines = [f"گزارش ناهنجاری‌ها (از {total} نمونه)", "="*40]
        lines.append(f"تعداد نمونه با حداقل یک ناهنجاری: {any_anom} ({100*any_anom/total:.2f}%)")
        for col in ['temp_C', 'voltage_V', 'current_A', 'signal_dBm', 'fuel_flow_kgps']:
            if f'anomaly_{col}' in df:
                cnt = df[f'anomaly_{col}'].sum()
                lines.append(f"  {col}: {cnt} ناهنجاری")
        return "\n".join(lines)