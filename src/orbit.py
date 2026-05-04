"""محاسبات مداری – موقعیت ECI و طول/عرض جغرافیایی با در نظر گرفتن پیش‌سِش J2"""

import numpy as np
from datetime import datetime
from src.config import Physics

class SatelliteOrbit:
    """
    مدار ماهواره با المان‌های کپلری و تصحیح J2 برای مدارهای LEO.
    از روابط بسته (تحلیلی) برای تغییرات آهسته گره صعودی و آرگومان حضیض استفاده می‌کند.
    """
    def __init__(self, a_km: float, e: float, i_deg: float, raan0_deg: float,
                 argp0_deg: float, M0_deg: float, epoch: datetime):
        """
        a_km   : نیم‌قطر بزرگ (km)
        e      : خروج از مرکز
        i_deg  : انحراف (درجه)
        raan0_deg : طول گره صعودی در مبدأ (درجه)
        argp0_deg : آرگومان حضیض در مبدأ (درجه)
        M0_deg    : آنومالی متوسط در مبدأ (درجه)
        epoch     : زمان مبدأ (datetime)
        """
        self.a = a_km
        self.e = e
        self.i = np.radians(i_deg)
        self.raan0 = np.radians(raan0_deg)
        self.argp0 = np.radians(argp0_deg)
        self.M0 = np.radians(M0_deg)
        self.epoch = epoch
        self.n0 = np.sqrt(Physics.GM_EARTH / self.a**3)   # حرکت متوسط (rad/s)
        
        # محاسبه نرخ‌های J2 (پیش‌سش)
        p = self.a * (1 - self.e**2)       # semi-latus rectum
        n = self.n0
        cos_i = np.cos(self.i)
        self.raan_dot = -1.5 * Physics.J2 * (Physics.R_EARTH**2 / p**2) * n * cos_i
        self.argp_dot = 1.5 * Physics.J2 * (Physics.R_EARTH**2 / p**2) * n * (2 - 2.5 * np.sin(self.i)**2)
        
    def _kepler_eccentric(self, M: np.ndarray, tol=1e-8) -> np.ndarray:
        """حل معادله کپلر برای آنومالی حقیقی (حتی برای e>0، با روش سریع نیوتن)"""
        if self.e == 0:
            return M
        E = M.copy()
        for _ in range(10):   # 10 تکرار کافی برای دقت 1e-8
            delta = E - self.e * np.sin(E) - M
            if np.max(np.abs(delta)) < tol:
                break
            E = E - delta / (1 - self.e * np.cos(E))
        nu = 2 * np.arctan2(np.sqrt(1+self.e)*np.sin(E/2), np.sqrt(1-self.e)*np.cos(E/2))
        return nu
    
    def get_position_eci(self, t_array: np.ndarray) -> np.ndarray:
        """
        محاسبه موقعیت در دستگاه ECI برای آرایه‌ای از زمان‌ها (بر حسب ثانیه از مبدأ)
        ورودی: t_array (1D array) – ثانیه از مبدأ
        خروجی: آرایه (3, n) از بردارهای موقعیت (km)
        """
        dt = t_array
        # به‌روزرسانی المان‌های وابسته به زمان
        raan = self.raan0 + self.raan_dot * dt
        argp = self.argp0 + self.argp_dot * dt
        M = self.M0 + self.n0 * dt
        nu = self._kepler_eccentric(M)
        
        r_mag = self.a * (1 - self.e**2) / (1 + self.e * np.cos(nu))
        
        # مختصات در صفحه مداری (perifocal)
        x_pf = r_mag * np.cos(nu)
        y_pf = r_mag * np.sin(nu)
        z_pf = np.zeros_like(dt)
        
        # ماتریس چرخش (3,3,n) به صورت برداری
        cos_raan = np.cos(raan); sin_raan = np.sin(raan)
        cos_i = np.cos(self.i); sin_i = np.sin(self.i)
        cos_argp = np.cos(argp); sin_argp = np.sin(argp)
        
        # روش: ضرب ماتریس 3x3 در هر نقطه
        def rot(pf_vec, cr, sr, ca, sa, ci, si):
            # pf_vec = [x, y, 0]
            x, y = pf_vec[0], pf_vec[1]
            # ستون اول ماتریس چرخش
            r11 = cr*ca - sr*sa*ci
            r12 = -cr*sa - sr*ca*ci
            r13 = sr*si
            r21 = sr*ca + cr*sa*ci
            r22 = -sr*sa + cr*ca*ci
            r23 = -cr*si
            r31 = sa*si
            r32 = ca*si
            r33 = ci
            return np.array([r11*x + r12*y, r21*x + r22*y, r31*x + r32*y])
        
        res = np.zeros((3, len(dt)))
        for i in range(len(dt)):
            res[:, i] = rot([x_pf[i], y_pf[i], z_pf[i]], 
                            cos_raan[i], sin_raan[i], cos_argp[i], sin_argp[i],
                            cos_i, sin_i)
        return res
    
    def get_lat_lon(self, t_seconds: np.ndarray) -> tuple:
        """
        تبدیل موقعیت ECI به عرض و طول جغرافیایی
        خروجی: (latitude_deg, longitude_deg) هر دو آرایه n تایی
        """
        r_eci = self.get_position_eci(t_seconds)  # shape (3,n)
        theta_g = Physics.OMEGA_EARTH * t_seconds   # چرخش زمین
        
        cos_t = np.cos(theta_g); sin_t = np.sin(theta_g)
        # چرخش معکوس به ECEF
        r_ecef_x = cos_t * r_eci[0] + sin_t * r_eci[1]
        r_ecef_y = -sin_t * r_eci[0] + cos_t * r_eci[1]
        r_ecef_z = r_eci[2]
        
        r_norm = np.sqrt(r_ecef_x**2 + r_ecef_y**2 + r_ecef_z**2)
        lat = np.arcsin(r_ecef_z / r_norm)
        lon = np.arctan2(r_ecef_y, r_ecef_x)
        return np.degrees(lat), np.degrees(lon)