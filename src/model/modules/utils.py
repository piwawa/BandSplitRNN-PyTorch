import torch

from typing import List, Tuple


def get_subband_indices(
        freqs: torch.Tensor,
        splits: List[Tuple[int, int]],
) -> List[Tuple[int, int]]:
    """
    """
    indices = []
    start_freq = 0
    start_index = 0
    for end_freq, step in splits:
        bands = torch.arange(start_freq + step, end_freq + step, step)
        start_freq = end_freq
        for band in bands:
            end_index = freqs[freqs < band].shape[0]
            indices.append((start_index, end_index))
            start_index = end_index
    indices.append((start_index, freqs.shape[0]))
    return indices


def get_fftfreq(
        sr: int = 44100,
        n_fft: int = 2048
) -> torch.Tensor:
    """
    Workaround of librosa.fft_frequencies
    """
    out = sr * torch.fft.fftfreq(n_fft)[:n_fft // 2 + 1]
    out[-1] = sr // 2
    return out


def freq2bands(
        bandsplits: List[Tuple[int, int]],
        sr: int = 44100,
        n_fft: int = 2048
) -> List[Tuple[int, int]]:
    """
    """
    freqs = get_fftfreq(sr=sr, n_fft=n_fft)
    band_indices = get_subband_indices(freqs, bandsplits)
    return band_indices


if __name__ == '__main__':
    freqs_splits = [
        (1000, 100),
        (4000, 250),
        (8000, 500),
        (16000, 1000),
        (20000, 2000),
    ]
    sr = 44100
    n_fft = 2048

    out = freq2bands(freqs_splits, sr, n_fft)

    assert sum(out) == n_fft // 2 + 1

    print(f"Input:\n{freqs_splits}\n{sr}\n{n_fft}\nOutput:{out}")