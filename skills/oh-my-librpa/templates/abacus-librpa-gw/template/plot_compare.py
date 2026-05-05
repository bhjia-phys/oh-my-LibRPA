#!/usr/bin/env python3
import os
import numpy as np
from typing import Iterable, Union, Tuple
import glob

import matplotlib.pyplot as plt


class KPathLinearizer:
    """object to manipulate path in reciprocal k space

    Special kpoints are recognized automatically.

    Args:
        kpts (list): the coordinates of k points
        recp_latt (3x3 array): the reciprocal lattice vectors, [b1, b2, b3].
            If parsed, it will be used to convert the kpts to Cartisian coordiantes.
    """

    def __init__(self, kpts, recp_latt=None, unify_x: bool = False):
        self._nkpts = len(kpts)
        if np.shape(kpts) != (self._nkpts, 3):
            raise ValueError("bad shape of parsed kpoints")
        self.kpts = np.array(kpts)
        if recp_latt is not None:
            self.kpts = np.matmul(kpts, recp_latt)
        self._ksegs = None
        self._unify_x = unify_x
        self._x = None
        self._special_x = None
        self._index_special_x = None
        self._find_ksegs()

    def _find_ksegs(self):
        self._ksegs = find_k_segments(self.kpts)

    def _compute_x(self):
        """calculate 1d abscissa of kpoints"""
        xs = []
        ispks = []
        accumu_l = 0.0
        for i, (st, ed) in enumerate(self._ksegs):
            l = np.linalg.norm(self.kpts[st, :] - self.kpts[ed, :])
            # remove duplicate
            if st not in ispks and st - 1 not in ispks:
                ispks.append(st)
            ispks.append(ed)
            # skip the starting point if it is the same as the endpoint of last segment
            skip = 0
            if i > 0:
                if st == self._ksegs[i - 1][1]:
                    skip = 1
            x = accumu_l + np.linalg.norm(
                self.kpts[st:ed + 1, :] - self.kpts[st, :], axis=1)[skip:]
            xs.extend(x)
            accumu_l += l
        self._x = np.array(xs)
        if self._unify_x:
            self._x /= self._x[-1]
        self._special_x = self._x[ispks]
        self._index_special_x = np.array(ispks)

    @property
    def x(self):
        """1d abscissa of points on kpath"""
        if self._x is None:
            self._compute_x()
        return self._x

    @property
    def special_x(self):
        """1d abscissa of points on kpath"""
        if self._special_x is None:
            self._compute_x()
        return self._special_x


def find_k_segments(kpts):
    """find line segments of parsed kpoint path

    Usually, the number of kpoints on one line segments is no less than 3.

    Args:
        kvec (array-like): the kpoint vectors to analysis, shape, (n,3)

    Returns:
        list, with tuple as members. Each tuple has 2 int members,
        the indices of kpoint vectors at the beginning and end of
        a line segment
    """
    ksegs = []
    nkpts = len(kpts)
    # the change in vector between two kpoints
    # dtype required
    kpts = np.array(kpts, dtype='float64')
    deltak = kpts[1:, :] - kpts[:-1, :]
    l = np.linalg.norm(deltak, axis=1)
    for i in range(nkpts - 1):
        if np.isclose(l[i], 0):
            deltak[i, :] = 0.
        else:
            deltak[i, :] = deltak[i, :] / l[i]
    # print(deltak)
    # dotprod[i] = (kpt[i+2] - kpt[i+1]) . (kpt[i+1] - kpt[i])
    dotprod = np.sum(deltak[1:, :] * deltak[:-1, :], axis=1)
    st = 0
    ed = 2
    while ed < nkpts:
        # a new segment when direction of delta vector changes
        # i.e. dot product is not 1 any more
        if not np.isclose(dotprod[ed - 2], 1.):
            ksegs.append((st, ed - 1))
            st = ed - 1
            # introduce a gap if the adjacent points are the same,
            # or the next segment starts from a new point
            if np.allclose(deltak[ed - 1, :], 0.) or \
                    (ed < nkpts - 1 and not np.isclose(dotprod[ed - 1], 1.)):
                st += 1
                ed += 1
        ed += 1
    if ed - st >= 2:
        ksegs.append((st, ed - 1))
    return ksegs


def read_band_output(
        *bfiles,
        bfiles_spin: Iterable[Union[str, os.PathLike]] = None,
        filter_k_before: int = 0,
        filter_k_behind: int = None,
        unit: str = 'ev', **kwargs):
    """read band output files and return a Band structure

    Note that all band energies are treated in the same spin channel,
    the resulting ``BandStructure`` object always has nspins=1

    Args:
        bfiles (str)
        bfiles_spin
        unit (str): unit of energies, default to ev
        filter_k_before
        filter_k_behind

        Other keyword argments parsed to the BandStructure object

    Returns:
        BandStructure, k-points
    """
    if len(bfiles) == 0:
        raise ValueError("need to parse at least one band output file")
    kpts = []
    occ = []
    ene = []
    for bf in bfiles:
        data = np.loadtxt(bf, unpack=True)
        kpts.extend(np.column_stack([data[1], data[2], data[3]]))
        occ.extend(np.transpose(data[4::2]))
        ene.extend(np.transpose(data[5::2]))
    kpts = np.array(kpts)

    if bfiles_spin is not None:
        kpts_spin = []
        occ_spin = []
        ene_spin = []
        for bf in bfiles_spin:
            data = np.loadtxt(bf, unpack=True)
            kpts_spin.extend(np.column_stack([data[1], data[2], data[3]]))
            occ_spin.extend(np.transpose(data[4::2]))
            ene_spin.extend(np.transpose(data[5::2]))
        kpts_spin = np.array(kpts_spin)

        # make sure that the spin up and down bands are describing the same k-points
        if len(kpts) != len(kpts_spin) and not np.allclose(kpts, kpts_spin):
            return ValueError("Inconsistent k-points for spin-up and spin-down band outputs")

    if filter_k_behind is None:
        filter_k_behind = len(kpts)
    kpts = kpts[filter_k_before:filter_k_behind, :]

    if bfiles_spin is None:
        occ = np.array([occ,])[:, filter_k_before:filter_k_behind, :]
        ene = np.array([ene,])[:, filter_k_before:filter_k_behind, :]
    else:
        occ = np.array([occ, occ_spin])[:, filter_k_before:filter_k_behind, :]
        ene = np.array([ene, ene_spin])[:, filter_k_before:filter_k_behind, :]

    return ene, occ, kpts


def get_band_edge(eigen, occ, edge: str = "vbm"):
    """"""
    nspins, nkpts, nbands = eigen.shape
    is_occ = occ > 0.5
    thres_degen = 5.0E-4  # in eV

    _vbm_sp_kp = np.zeros((nspins, nkpts))
    _cbm_sp_kp = np.zeros((nspins, nkpts))
    _ivbm_sp_kp = np.zeros((nspins, nkpts), dtype=int)
    _icbm_sp_kp = np.zeros((nspins, nkpts), dtype=int)
    _vbm_sp = np.zeros((nspins))
    _cbm_sp = np.zeros((nspins))
    _ivbm_sp = np.zeros((nspins, 2), dtype=int)
    _icbm_sp = np.zeros((nspins, 2), dtype=int)
    _ivbm = np.zeros(3, dtype=int)
    _icbm = np.zeros(3, dtype=int)

    _vbm_sp_kp[:, :] = -np.inf
    _cbm_sp_kp[:, :] = np.inf
    _vbm_sp[:] = -np.inf
    _cbm_sp[:] = np.inf
    _vbm = -np.inf
    _cbm = np.inf

    for isp in range(nspins):
        for ik in range(nkpts):
            for ib, ibr in zip(range(nbands), reversed(range(nbands))):
                # use thres_degen such that when degenerate bands are met,
                # we always use the larger (smaller) index for VBM (CBM)
                if is_occ[isp, ik, ib] and (
                        eigen[isp, ik, ib] > _vbm_sp_kp[isp, ik] or
                        abs(eigen[isp, ik, ib] - _vbm_sp_kp[isp, ik]) < thres_degen):
                    _vbm_sp_kp[isp, ik] = eigen[isp, ik, ib]
                    _ivbm_sp_kp[isp, ik] = ib
                if not is_occ[isp, ik, ibr] and (
                        eigen[isp, ik, ibr] < _cbm_sp_kp[isp, ik] or
                        abs(eigen[isp, ik, ibr] - _cbm_sp_kp[isp, ik]) < thres_degen):
                    _cbm_sp_kp[isp, ik] = eigen[isp, ik, ibr]
                    _icbm_sp_kp[isp, ik] = ibr
            if _vbm_sp_kp[isp, ik] > _vbm_sp[isp]:
                _vbm_sp[isp] = _vbm_sp_kp[isp, ik]
                _ivbm_sp[isp, :] = [ik, _ivbm_sp_kp[isp, ik]]
            if _cbm_sp_kp[isp, ik] < _cbm_sp[isp]:
                _cbm_sp[isp] = _cbm_sp_kp[isp, ik]
                _icbm_sp[isp, :] = [ik, _icbm_sp_kp[isp, ik]]
        if _vbm_sp[isp] > _vbm:
            _vbm = _vbm_sp[isp]
            _ivbm[:] = [isp, *_ivbm_sp[isp]]
        if _cbm_sp[isp] < _cbm:
            _cbm = _cbm_sp[isp]
            _icbm[:] = [isp, *_icbm_sp[isp]]
    if edge == "vbm":
        return _vbm
    if edge == "cbm":
        return _cbm


def get_recp_latt_from_geometry(fn_geometry):
    """get reciprocal lattice vectors of from aims geometry file"""
    latt = []
    with open(fn_geometry, 'r') as h:
        lines = h.readlines()
        for l in lines:
            if l.strip().startswith("lattice_vector"):
                latt.append(list(map(float, l.split()[1:4])))
    if len(latt) != 3:
        raise ValueError("Lattice vectors less than 1, check your geometry file!")
    latt = np.array(latt)
    return np.cross(latt[(1, 2, 0), :], latt[(2, 0, 1), :]) / np.linalg.det(latt) * 2.0E0 * np.pi

def read_abacus(filename):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            columns_data = []
            for line in lines:
                parts = line.split()
                if len(parts) < 3:  # 确保行中有足够的数据
                    continue
                columns_data.append([float(part) for part in parts[2:]])  # 从第三列开始读取，转换为浮点数
            return [list(column) for column in zip(*columns_data)], columns_data[0][0]
    except FileNotFoundError:
        print(f"文件 {filename} 未找到。")
        return None
    except Exception as e:
        print(f"读取文件时发生错误：{e}")
        return None

def read_abacus_kpoints(filename):
    flag = 0
    with open(filename, 'r') as file:
        lines = file.readlines()
        columns_data = []
        for line in lines:
            if line.strip():
                parts = line.split()
                if parts[0] == '1': 
                    flag = 1
                if flag == 1:
                    columns_data.append([float(part) for part in parts[1:4]]) 
        return columns_data

def read_occ_abacus(bandout_file='band_out'):
    data = {
        'occ': []
    }
    with open(bandout_file, 'r') as bo:
        band_out_lines = bo.readlines()
    start_reading = False

    for line in band_out_lines:
        parts = line.split()
        if start_reading:
            if len(line.split()) < 4:
                break
            if len(parts) == 4:
                data['occ'].append(float(parts[1]))
        elif len(parts) == 4:
            start_reading = True
            data['occ'].append(float(parts[1]))
    return data['occ']

# input parameters here    
aims_file="../../../aims_band/GW_band*"
abacus_file="GW_band_spin_1.dat"
title=r'GaAs $G_0W_0$@PBE k888'
#title=r'GaAs HF@PBE k888'
nbands_abacus=30
# Load the common geometry file, use that under pbesol directory
recp_latt = get_recp_latt_from_geometry("geometry.in")

# Read FHI-aims GW control and band data files
band_files_aims = sorted(glob.glob(aims_file))
ene_aims, occ_aims, kpts_aims = read_band_output(*band_files_aims, unit="eV")
vbm_aims = get_band_edge(ene_aims, occ_aims, "vbm")
kp_aims = KPathLinearizer(kpts_aims, recp_latt)

fig, ax = plt.subplots(1, 1, figsize=(10, 9))
 # plot DFT bands, only draw spin 0 channel
for ib in range(ene_aims.shape[-1]):
    label = None
    if ib == 0:
        label = "FHI-aims intermediate"
    ax.plot(kp_aims.x, ene_aims[0, :, ib] - vbm_aims, label=label, color="k", ls="-")
 #plot HSE bands, only draw spin 0 channel
    

ene_librpa, occ_librpa, kpts_librpa = read_band_output(abacus_file, unit="eV")
occ_abacus = read_occ_abacus()
for i in range(len(occ_librpa[0])):
    for j in range(len(occ_librpa[0][0])):
        if(occ_abacus[j] != 0.):
            occ_librpa[0][i][j]=occ_abacus[j]
vbm_librpa = get_band_edge(ene_librpa, occ_librpa, "vbm")
kp_librpa = KPathLinearizer(kpts_librpa, recp_latt)
for ib in range(nbands_abacus):#ene_librpa.shape[-1]
    label = None
    if ib == 0:
        label = "ABACUS+LibRPA TZDP"
    
    ax.plot(kp_librpa.x, ene_librpa[0, :, ib] - vbm_librpa, label=label, color="red",ls='--')


font = {'family' : 'serif',
'weight' : 'normal',
'size'   : 23,
}
# draw tick label, using DFT special kpoints
ax.xaxis.set_ticks(kp_aims.special_x)
ax.xaxis.grid(color='k')

ax.set_ylabel("Energy [eV]",font)
ax.set_xlabel("Kpoints",font)
#ax.set_title(r'GaN $G_0W_0$@PBE', font)  
ax.set_title(title, font)  
ax.set_xlim(kp_aims.x[0], kp_aims.x[-1])
ax.set_ylim(ymin=-27, ymax=25)
ax.axhline(0.0, ls=":", color="k")
ax.legend(prop=font)
high_symmetry_positions=kp_aims.special_x
high_symmetry=['G', 'K', 'L', 'U', 'W', 'W2', 'X']
plt.xticks(high_symmetry_positions, high_symmetry)
ax.set_xticklabels(high_symmetry, fontsize=20)
ax.tick_params(axis='y', labelsize=20)
fig.savefig("gwband.png", dpi=300)
#plt.show()
