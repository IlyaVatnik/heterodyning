# -*- coding: utf-8 -*-
"""
Created on Wed Jun  3 18:51:02 2026

@author: Dima, Ilya
"""

import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy.signal import hilbert, butter, sosfiltfilt, find_peaks
from scipy.ndimage import gaussian_filter1d
import os 
import re

__version__='1.0'
__date__='2026.06.09'

class TraceAnalyzer2D:
    def __init__(self, filepath, sweep_period=0.5e-3):
        self.filepath = filepath
        self.sweep_period = sweep_period
        
        
    

    def load_and_process(self, highpass_cutoff_hz=50e3): # Снизили до 15 кГц!
        with open(self.filepath, 'rb') as f:
            raw_signal, xinc, xorigin = pickle.load(f)
            
        self.time_step = xinc
        self.start_time = xorigin
        self.sampling_rate = 1.0 / self.time_step
        
        self.samples_per_fragment = int(self.sweep_period / self.time_step)
        num_fragments = len(raw_signal) // self.samples_per_fragment
        
        self.truncated_raw_signal = raw_signal[:num_fragments * self.samples_per_fragment]
        fragments_2d = self.truncated_raw_signal.reshape((num_fragments, self.samples_per_fragment))
        
        nyq = 0.5 * self.sampling_rate
        normal_cutoff = highpass_cutoff_hz / nyq
        sos = butter(N=4, Wn=normal_cutoff, btype='highpass', output='sos')
        filtered_2d = sosfiltfilt(sos, fragments_2d, axis=1)
        
        analytic_signal_2d = hilbert(filtered_2d, axis=1)
        raw_envelope = np.abs(analytic_signal_2d)
        
        # НОВОЕ: Мягкое сглаживание огибающей (убивает "волосатость" и ложные пики).
        # sigma=5 означает окно сглаживания в 5 отсчетов. При необходимости можно увеличить до 10-20.
        self.intensity_2d = gaussian_filter1d(raw_envelope, sigma=5, axis=1)
        
        self.slow_times = np.arange(num_fragments) * self.sweep_period + self.start_time
        return self.slow_times, self.intensity_2d

    def calibrate_axis(self, ref_wavelengths, known_coeff=None, prominence_rel=0.3):
        num_scans, num_samples = self.intensity_2d.shape
        self.wavelengths_2d = np.zeros_like(self.intensity_2d)
        
        self.calculated_coeffs = []
        self.calculated_wave0s = []
        times_array = np.arange(num_samples) * self.time_step
        
        fallback_coeff = known_coeff if known_coeff else 100000.0 
        
        # 1. ОБЯЗАТЕЛЬНАЯ СОРТИРОВКА длин волн!
        # Время t_peaks всегда отсортировано по возрастанию, 
        # значит и длины волн должны идти строго по возрастанию (от меньшей к большей).
        refs_sorted = sorted(ref_wavelengths)
        num_refs = len(refs_sorted)
        
        for i in range(num_scans):
            scan = self.intensity_2d[i]
            prominence_thr = np.max(scan) * prominence_rel
            
            peaks, properties = find_peaks(scan, prominence=prominence_thr) #distance=num_samples//1000
            
            top_peaks = sorted(peaks, key=lambda x: properties['prominences'][np.where(peaks == x)[0][0]], reverse=True)[:num_refs]
            top_peaks.sort()
            
            is_valid_scan = False
            
            if len(top_peaks) == num_refs:
                t_peaks = np.array(top_peaks) * self.time_step
                
                if num_refs == 2:
                    # Теперь мы точно знаем, что w1 < w2, так как список отсортирован
                    w1, w2 = refs_sorted
                    t1, t2 = t_peaks
                    actual_dt = t2 - t1
                    
                    # # 2. УМНЫЙ SANITY CHECK
                    # # Рассчитываем, сколько примерно времени должно пройти между этими конкретными лазерами
                    expected_dt = (w2 - w1) / fallback_coeff
                    
                    # # Требуем, чтобы реальное время было хотя бы > 20% от ожидаемого.
                    # # Это позволяет скорости интерогатора "плавать" очень сильно,
                    # # но при этом гарантированно убивает ложные срабатывания на соседних микро-шумах.
                    if actual_dt > (expected_dt * 0.2):
                        coeff = (w2 - w1) / actual_dt
                        wave0 = w1 - coeff * t1
                        
                        if 1500.0 < wave0 < 1570.0 and coeff > 0:
                            is_valid_scan = True
                            
                elif num_refs == 1:
                    w1 = refs_sorted[0]
                    t1 = t_peaks[0]
                    coeff = self.calculated_coeffs[-1] if self.calculated_coeffs else fallback_coeff
                    wave0 = w1 - coeff * t1
                    
                    if 1500.0 < wave0 < 1570.0 and coeff > 0:
                        is_valid_scan = True
            
            # if not is_valid_scan:
            #     coeff = self.calculated_coeffs[-1] if self.calculated_coeffs else fallback_coeff
            #     wave0 = self.calculated_wave0s[-1] if self.calculated_wave0s else 1528.0
            
            self.calculated_coeffs.append(coeff)
            self.calculated_wave0s.append(wave0)
            self.wavelengths_2d[i, :] = times_array * coeff + wave0
            
        mean_coeff = np.mean(self.calculated_coeffs)
        return self.wavelengths_2d, mean_coeff
    
    @property
    def wavelengths_1d(self):
        # Берем медианные значения начала и конца скана, чтобы исключить случайные выбросы
        # Берем медианные значения начала и конца скана, чтобы исключить случайные выбросы
        wvl_min = np.median(self.wavelengths_2d[:, 0])
        wvl_max = np.median(self.wavelengths_2d[:, -1])
        
        # Узнаем количество точек в одном скане
        num_points = self.intensity_2d.shape[1]
        
        return np.linspace(wvl_min, wvl_max, num_points)
    
    
    # ==========================================
    # ФУНКЦИИ ОТРИСОВКИ СИГНАЛОВ
    # ==========================================
    # def plot_2d_map(self):
    #     if not hasattr(self, 'wavelengths_2d'):
    #         raise ValueError("Сначала вызовите метод calibrate_axis()")
            
    #     plt.figure(figsize=(12, 6))
        
    #     # Размножаем 1D время в 2D массив
    #     Y_2d = np.broadcast_to(self.slow_times[:, None], self.intensity_2d.shape)
        

    #     plot_data = self.intensity_2d 
        
    #     
    #     vmin = np.percentile(plot_data, 10.0) 
    #     vmax = np.percentile(plot_data, 99.9) 
        
    #     # Рисуем сырые полигоны
    #     c = plt.pcolormesh(self.wavelengths_2d, Y_2d, plot_data, 
    #                        shading='nearest', cmap='turbo', 
    #                        norm=colors.Normalize(vmin=vmin, vmax=vmax))
        
    #     подписи
    #     plt.colorbar(c, label='Интенсивность биений (Корневая шкала)')
    #     plt.xlabel('Длина волны (нм) [Сырая калибровка]')
    #     plt.ylabel('Время эксперимента (с)')
    #     plt.title('Спектрограмма сигналов')
        
    #     # Жестко фиксируем границы оси X, чтобы защититься от сумасшедших сканов
    #     wvl_min = np.median(self.wavelengths_2d[:, 0])
    #     wvl_max = np.median(self.wavelengths_2d[:, -1])
    #     if wvl_min > wvl_max:
    #         wvl_min, wvl_max = wvl_max, wvl_min
    #     plt.xlim(wvl_min, wvl_max)
        
    #     # Вместо tight_layout() используем более безопасный метод для сложных 2D сеток
    #     plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
        
    #     plt.show()



    def plot_2d_map(self):
            if not hasattr(self, 'wavelengths_2d'):
                raise ValueError("Сначала вызовите метод calibrate_axis()")
                
            plt.figure(figsize=(12, 6))
            
            # МАГИЯ КОНТРАСТА (оставляем корень)
            plot_data = self.intensity_2d 
            vmin = np.percentile(plot_data, 70.0) 
            vmax = np.percentile(plot_data, 100.0) 
            
            # Находим границы для осей
            wvl_min = np.median(self.wavelengths_2d[:, 0])
            wvl_max = np.median(self.wavelengths_2d[:, -1])
            if wvl_min > wvl_max:
                wvl_min, wvl_max = wvl_max, wvl_min
                
            t_min = self.slow_times[0]
            t_max = self.slow_times[-1]
    
            # ИСПОЛЬЗУЕМ IMSHOW ВМЕСТО PCOLORMESH
            # extent - растягивает картинку на физические координаты осей
            # aspect='auto' - позволяет графику быть прямоугольным, а не квадратным
            # origin='lower' - переворачивает картинку, чтобы время росло снизу вверх
            c = plt.imshow(plot_data, 
                           extent=[wvl_min, wvl_max, t_min, t_max], 
                           aspect='auto', 
                           origin='lower', 
                           cmap='turbo', 
                           norm=colors.Normalize(vmin=vmin, vmax=vmax),
                           interpolation='nearest') # Запрещаем размытие пиков
            
            #plt.colorbar(c, label='Интенсивность биений (Корневая шкала)')
            plt.xlabel('Длина волны (нм)')
            plt.ylabel('Время эксперимента (с)')
            # plt.title('Спектрограмма сигналов (Сверхбыстрый рендер)')
            
            plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.15)
            plt.show()

    def plot_signal_vs_time(self, mode='envelope', t_start=None, t_end=None):
        """
        1. Отрисовка непрерывного 1D сигнала от абсолютного времени эксперимента.
        :param mode: 'envelope' (огибающая биений) или 'raw' (сырой сигнал с осциллографа)
        :param t_start: Начало окна отрисовки в секундах (опционально)
        :param t_end: Конец окна отрисовки в секундах (опционально)
        """
        plt.figure(figsize=(12, 4))
        
        total_samples = len(self.truncated_raw_signal)
        continuous_time = np.arange(total_samples) * self.time_step + self.start_time
        
        if mode == 'envelope':
            signal = self.intensity_2d.flatten()
            ylabel = 'Интенсивность огибающей (у.е.)'
        elif mode == 'raw':
            signal = self.truncated_raw_signal
            ylabel = 'Сырой сигнал (В)'
        else:
            raise ValueError("Параметр mode должен быть 'envelope' или 'raw'")

        # Обрезка по времени, если заданы t_start и t_end
        mask = np.ones(total_samples, dtype=bool)
        if t_start is not None:
            mask &= (continuous_time >= t_start)
        if t_end is not None:
            mask &= (continuous_time <= t_end)
            
        plt.plot(continuous_time[mask], signal[mask], color='blue' if mode=='envelope' else 'gray', linewidth=0.8)
        plt.xlabel('Абсолютное время (с)')
        plt.ylabel(ylabel)
        plt.title(f'Полный временной трейс ({mode})')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def plot_spectrum_at_time(self, target_time):
        """
        2. Отрисовка сигнала (спектра) от длины волны для заданного момента времени (срез 2D матрицы).
        :param target_time: Время эксперимента в секундах
        """
        if not hasattr(self, 'wavelengths_2d'):
            raise ValueError("Сначала вызовите calibrate_axis()")
            
        # Находим индекс скана, время которого ближе всего к запрошенному target_time
        idx = np.argmin(np.abs(self.slow_times - target_time))
        actual_time = self.slow_times[idx]
        
        wvls = self.wavelengths_2d[idx]
        intensity = self.intensity_2d[idx]
        
        plt.figure(figsize=(10, 4))
        plt.plot(wvls, intensity, color='green')
        plt.xlabel('Длина волны (нм)')
        plt.ylabel('Интенсивность биений (у.е.)')
        plt.title(f'Спектр (срез на времени t ≈ {actual_time:.4f} с)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

    def plot_dynamics_at_wavelength(self, target_wavelength):
        """
        3. Отрисовка эволюции сигнала во времени строго на заданной длине волны.
        Так как оси длин волн динамические, используется интерполяция значений.
        :param target_wavelength: Целевая длина волны в нм
        """
        if not hasattr(self, 'wavelengths_2d'):
            raise ValueError("Сначала вызовите calibrate_axis()")
            
        intensity_over_time = []
        
        for i in range(len(self.slow_times)):
            wvls = self.wavelengths_2d[i]
            ints = self.intensity_2d[i]
            
            # Функция np.interp требует, чтобы ось X (wvls) строго возрастала.
            # На случай, если перестройка идет от больших длин к меньшим:
            if wvls[0] > wvls[-1]:
                val = np.interp(target_wavelength, wvls[::-1], ints[::-1])
            else:
                val = np.interp(target_wavelength, wvls, ints)
                
            intensity_over_time.append(val)
            
        plt.figure(figsize=(10, 4))
        plt.plot(self.slow_times, intensity_over_time, color='red')
        plt.xlabel('Абсолютное время (с)')
        plt.ylabel('Интенсивность биений (у.е.)')
        plt.title(f'Временная динамика на длине волны $\\lambda = {target_wavelength}$ нм')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

if __name__ == '__main__':
    # Базовая загрузка и калибровка
    analyzer = TraceAnalyzer2D("data\\Pure=1545, AFR,OSA.trace")
    analyzer.load_and_process()
    #analyzer.calibrate_axis(ref_wavelengths=[1531.38, 1550.17])
    ref_wave1=1532.8323
    ref_wave2=1545.0
    _, avg_coeff = analyzer.calibrate_axis(ref_wavelengths=[ref_wave1, ref_wave2])
    times_array = analyzer.slow_times
    intensity_matrix = analyzer.intensity_2d
    wavelengths_2d_matrix = analyzer.wavelengths_2d
    mean_coeff = avg_coeff
    wl1d=analyzer.wavelengths_1d
    # ---------------------------------------------------------
    # 1. Построение сигнала от времени
    # ---------------------------------------------------------
    # Можно вывести сырой сигнал (чтобы увидеть сами биения-осцилляции) 
    # для первых 2 миллисекунд:
    analyzer.plot_signal_vs_time(mode='raw', t_start=0, t_end=2e-3)
    
    # Или вывести выделенную огибающую (после Гильберта) целиком:
    analyzer.plot_signal_vs_time(mode='envelope')
    
    # ---------------------------------------------------------
    # 2. Спектр в конкретный момент времени
    # ---------------------------------------------------------
    # Допустим, мы хотим посмотреть, как выглядел спектр через 1 секунду после старта:
    analyzer.plot_spectrum_at_time(target_time=0.0)
    
    # ---------------------------------------------------------
    # 3. Динамика конкретной длины волны
    # ---------------------------------------------------------
    # Смотрим, как менялась интенсивность лазера ровно на 1550.17 нм на протяжении всего эксперимента:
    analyzer.plot_dynamics_at_wavelength(target_wavelength=1550.18) 
    
    # 1. Анализируем калибровочный файл (сейчас)
    calib_file = "data\\Pure=1545, AFR,OSA.trace"
    analyzer_test = TraceAnalyzer2D(calib_file)
    analyzer_test.load_and_process()
    
    # Передаем ДВЕ известные длины волны. 
    # Алгоритм вычислит time_to_wave_coeff динамически для каждого скана!
    
    
    analyzer.plot_2d_map()

    # Сохраняем avg_coeff для будущих экспериментов
    print(f"Коэффициент перестройки: {avg_coeff} нм/с")
    
    # source_root='data//2lasers'
    # all_items = os.listdir(source_root)
    # avg_coef_array=[]
    # ref_wave1=1532.8323
    # for item in all_items:
    #     item_path = os.path.join(source_root, item)
    #     analyzer = TraceAnalyzer2D(item_path)
    #     analyzer.load_and_process()
    #     #analyzer.calibrate_axis(ref_wavelengths=[1531.38, 1550.17])
    #     ref_wave2=analyzer.parse_wavelength_from_filename(item_path)
    #     _, avg_coeff = analyzer.calibrate_axis(ref_wavelengths=[ref_wave1, ref_wave2])
    #     avg_coef_array.append([ref_wave2,avg_coeff])
    # avg_coef_array=np.asarray(avg_coef_array)
    # plt.figure()
    # plt.xlabel('длина волны второго лазера')
    # plt.ylabel('нм/мсек')
    # #plt.yscale('log')
    # plt.scatter(avg_coef_array[:,0], avg_coef_array[:,1]/1000)
'''    
    # 2. Анализ экспериментального файла со случайным лазером
    rfl_file = "data\\RFL_experiment.trace"
    analyzer_rfl = TraceAnalyzer2D(rfl_file)
    analyzer_rfl.load_and_process()
    
    # Передаем ОДНУ якорную длину волны (1531.38) и коэффициент, полученный на Шаге 1.
    # Алгоритм найдет якорный пик и подстроит wave0, чтобы компенсировать джиттер интерогатора
    analyzer_rfl.calibrate_axis(ref_wavelengths=[1531.38], known_coeff=avg_coeff)

    # Строим спектрограмму RFL
    analyzer_rfl.plot_2d_map()
'''        


