#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

mpl.rcParams.update({
    'figure.dpi': 180,
    'savefig.dpi': 450,
    'font.family': 'DejaVu Serif',
    'mathtext.fontset': 'stix',
    'axes.linewidth': 1.0,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.major.size': 5,
    'ytick.major.size': 5,
    'xtick.major.width': 1.0,
    'ytick.major.width': 1.0,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Plot a periodic GW band structure with a compact paper-style near-gap view.'
    )
    parser.add_argument('--run-dir', required=True, help='Run directory containing GW outputs.')
    parser.add_argument('--gw-file', help='GW band file. Default: <run-dir>/GW_band_spin_1.dat')
    parser.add_argument('--band-out-file', help='band_out file. Default: <run-dir>/band_out')
    parser.add_argument('--kpath-file', help='band_kpath_info file. Default: <run-dir>/band_kpath_info')
    parser.add_argument('--kpt-nscf-file', help='KPT_nscf file. Default: <run-dir>/KPT_nscf')
    parser.add_argument('--outdir', help='Output directory. Default: <run-dir>/plots')
    parser.add_argument('--prefix', default='GW_band_paper', help='Output filename prefix.')
    parser.add_argument('--title', default=r'$G_0W_0$ band structure', help='Top-left figure title.')
    parser.add_argument('--kpath-label-text', default='', help='Optional k-path text shown below the title.')
    parser.add_argument('--valence-bands', type=int, default=4, help='How many valence bands to plot.')
    parser.add_argument('--conduction-bands', type=int, default=4, help='How many conduction bands to plot.')
    parser.add_argument('--cbm-search-window', type=int, default=6, help='How many low-lying conduction bands to search for the CBM.')
    parser.add_argument('--ymin', type=float, default=-6.2, help='Lower y limit in eV after shifting to VBM.')
    parser.add_argument('--ymax', type=float, default=4.2, help='Upper y limit in eV after shifting to VBM.')
    return parser.parse_args()


def read_occ_from_band_out(path: Path) -> np.ndarray:
    occ = []
    started = False
    for line in path.read_text().splitlines():
        parts = line.split()
        if not started:
            if len(parts) == 2:
                started = True
            continue
        if len(parts) != 4:
            if occ:
                break
            continue
        occ.append(float(parts[1]))
    return np.array(occ)


def read_gw(path: Path):
    data = np.loadtxt(path)
    return data[:, 1:4], data[:, 4::2], data[:, 5::2]


def read_band_kpath_info(path: Path) -> np.ndarray:
    lines = path.read_text().splitlines()
    nk = int(lines[0].split()[-1])
    return np.array([[float(x) for x in line.split()] for line in lines[1:1 + nk]])


def cumulative_x(kpts: np.ndarray) -> np.ndarray:
    d = np.diff(kpts, axis=0)
    return np.concatenate([[0.0], np.cumsum(np.linalg.norm(d, axis=1))])


def parse_kpt_labels(path: Path):
    labels, counts = [], []
    mode = None
    for line in path.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith('K_POINTS'):
            continue
        if s.isdigit():
            continue
        if s in ('Line', 'Gamma', 'MP'):
            mode = s
            continue
        if mode != 'Line':
            continue
        left, *right = line.split('#', 1)
        parts = left.split()
        if len(parts) >= 4:
            counts.append(int(float(parts[3])))
            lab = right[0].strip() if right else f'P{len(labels) + 1}'
            labels.append('Γ' if lab.upper() in ('G', 'GAMMA', 'Γ') else lab)
    return labels, counts


def require_file(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f'Missing required file: {path}')


def main() -> None:
    args = parse_args()
    run = Path(args.run_dir).expanduser().resolve()
    plotdir = Path(args.outdir).expanduser().resolve() if args.outdir else (run / 'plots')
    plotdir.mkdir(parents=True, exist_ok=True)

    gw_file = Path(args.gw_file).expanduser().resolve() if args.gw_file else (run / 'GW_band_spin_1.dat')
    band_out_file = Path(args.band_out_file).expanduser().resolve() if args.band_out_file else (run / 'band_out')
    kpath_file = Path(args.kpath_file).expanduser().resolve() if args.kpath_file else (run / 'band_kpath_info')
    kpt_nscf_file = Path(args.kpt_nscf_file).expanduser().resolve() if args.kpt_nscf_file else (run / 'KPT_nscf')

    for path in (gw_file, band_out_file, kpath_file, kpt_nscf_file):
        require_file(path)

    occ = read_occ_from_band_out(band_out_file)
    kpts_gw, _aux_gw, ene_gw = read_gw(gw_file)
    kpts_path = read_band_kpath_info(kpath_file)
    labels, counts = parse_kpt_labels(kpt_nscf_file)

    if len(kpts_gw) != len(kpts_path):
        raise ValueError(f'k-point count mismatch: GW={len(kpts_gw)} band_kpath_info={len(kpts_path)}')

    x = cumulative_x(kpts_path)
    special_idx = [0]
    acc = 0
    for c in counts[:-1]:
        acc += c
        special_idx.append(acc)
    special_idx = np.array(special_idx, dtype=int)
    special_x = x[special_idx]
    labels = labels[:len(special_x)]

    occ_mask_1d = occ > 0.5
    nocc = int(np.count_nonzero(occ_mask_1d))
    if nocc <= 0:
        raise ValueError('Failed to determine occupied bands from band_out.')

    occ2d = np.tile(occ_mask_1d.reshape(1, -1), (ene_gw.shape[0], 1))
    vbm = np.max(np.where(occ2d, ene_gw, -np.inf))

    cbm_band_lo = nocc
    cbm_band_hi = min(ene_gw.shape[1], nocc + max(1, args.cbm_search_window))
    if cbm_band_lo >= cbm_band_hi:
        raise ValueError('No conduction bands available for the restricted CBM search window.')

    cbm = np.min(ene_gw[:, cbm_band_lo:cbm_band_hi])
    cbm_loc = np.argwhere(np.isclose(ene_gw[:, cbm_band_lo:cbm_band_hi], cbm, atol=1e-8))[0]
    cbm_k = int(cbm_loc[0])
    cbm_b = int(cbm_band_lo + cbm_loc[1])

    b0 = max(0, nocc - max(1, args.valence_bands))
    b1 = min(ene_gw.shape[1], nocc + max(1, args.conduction_bands))
    plot_bands = list(range(b0, b1))
    shifted = ene_gw - vbm
    gap = cbm - vbm

    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    for sx in special_x:
        ax.axvline(sx, color='0.82', lw=0.8, zorder=0)
    ax.axhline(0.0, color='0.35', lw=1.0, ls='--', zorder=0)

    line_color = '#163d6b'
    for ib in plot_bands:
        is_edge = (ib == nocc - 1) or (ib == cbm_b)
        ax.plot(
            x,
            shifted[:, ib],
            color=line_color,
            lw=1.55 if is_edge else 1.15,
            alpha=0.95 if is_edge else 0.88,
        )

    if 0.0 < gap < 10.0:
        ax.scatter([x[0], x[cbm_k]], [0.0, gap], s=18, color='#8b1e3f', zorder=5)
        ax.text(
            0.985,
            0.965,
            fr'$E_g^{{GW}} = {gap:.3f}\ \mathrm{{eV}}$',
            transform=ax.transAxes,
            ha='right',
            va='top',
            fontsize=12,
            color='#8b1e3f',
            bbox=dict(boxstyle='round,pad=0.18', fc='white', ec='0.85', lw=0.5, alpha=0.92),
        )

    ax.set_xlim(x[0], x[-1])
    ax.set_ylim(args.ymin, args.ymax)
    ax.set_ylabel(r'$E - E_{\mathrm{VBM}}$ (eV)', fontsize=15)
    ax.set_xticks(special_x)
    ax.set_xticklabels(labels, fontsize=13)
    ax.tick_params(axis='y', labelsize=12)
    ax.text(0.015, 0.97, args.title, transform=ax.transAxes, ha='left', va='top', fontsize=13)
    if args.kpath_label_text:
        ax.text(0.015, 0.905, args.kpath_label_text, transform=ax.transAxes, ha='left', va='top', fontsize=10.5, color='0.28')
    for spine in ax.spines.values():
        spine.set_color('0.1')
    fig.subplots_adjust(left=0.12, right=0.985, bottom=0.16, top=0.94)

    png = plotdir / f'{args.prefix}.png'
    pdf = plotdir / f'{args.prefix}.pdf'
    fig.savefig(png, bbox_inches='tight')
    fig.savefig(pdf, bbox_inches='tight')
    plt.close(fig)

    summary = plotdir / f'{args.prefix}_summary.txt'
    summary.write_text(
        '\n'.join([
            f'Number of occupied bands from band_out: {nocc}',
            f'VBM (absolute): {vbm:.6f} eV',
            f'CBM (restricted near-gap search): {cbm:.6f} eV',
            f'GW gap (restricted near-gap search): {gap:.6f} eV',
            f'CBM candidate: k={cbm_k + 1}, band={cbm_b + 1}, kfrac={kpts_gw[cbm_k].tolist()}',
            f'Plotted bands: {[b + 1 for b in plot_bands]}',
            f'PNG: {png}',
            f'PDF: {pdf}',
        ]) + '\n'
    )
    print(summary.read_text(), end='')


if __name__ == '__main__':
    main()
