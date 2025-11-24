import numpy as np
from scipy.signal import hilbert
import matplotlib.pyplot as plt

def phase_demod_hilbert(x, fs, f0=None, return_amp=False, detrend_carrier=True):
    """
    Фазовая демодуляция синусоидального сигнала через преобразование Гильберта.

    Параметры
    ---------
    x : 1D array
        Входной сигнал (вещественный).
    fs : float
        Частота дискретизации, Гц.
    f0 : float or None
        Несущая частота, Гц. Если задана, фаза будет относительно этой несущей.
        Если None, фаза возвращается как есть (полная).
    return_amp : bool
        Если True, дополнительно вернуть огибающую (амплитуду).
    detrend_carrier : bool
        Если True и f0 is None, то из фазы вычитается линейный тренд
        (оценка «несущей» по МНК), остаётся только медленная составляющая.

    Возвращает
    ----------
    phi : 1D array
        Размотанная фаза (рад).
    amp : 1D array, опционально
        Амплитуда (огибающая), если return_amp=True.
    """
    x = np.asarray(x)

    # 1) Аналитический сигнал
    z = hilbert(x)

    # 2) Фаза и амплитуда
    phi = np.unwrap(np.angle(z))
    amp = np.abs(z)

    t = np.arange(len(x)) / fs

    if f0 is not None:
        # Вычесть известную несущую: phi(t) = (общая фаза) - 2π f0 t
        phi = phi - 2 * np.pi * f0 * t
    elif detrend_carrier:
        # Оценить линейный тренд фазы (эффективная несущая) и вычесть
        A = np.vstack([t, np.ones_like(t)]).T
        k, b = np.linalg.lstsq(A, phi, rcond=None)[0]  # phi ≈ k t + b
        phi = phi - (k * t + b)

    if return_amp:
        return phi, amp
    else:
        return phi


# Пример использования:
if __name__ == "__main__":
    fs = 10_000      # Гц
    f0 = 1000        # несущая, Гц
    N = 10_000
    t = np.arange(N) / fs

    # Синус с фазовым скачком в моменте t = 0.5 c на +π/2
    phi_true = np.zeros_like(t)
    phi_true[t >= 0.5] += np.pi / 2

    x = np.cos(2 * np.pi * f0 * t + phi_true)

    # Демодуляция (фаза относительно известной несущей)
    phi_est = phase_demod_hilbert(x, fs, f0=f0)

    # Теперь phi_est ≈ phi_true (с точностью до шума/краевых эффектов)
    plt.plot(phi_est)