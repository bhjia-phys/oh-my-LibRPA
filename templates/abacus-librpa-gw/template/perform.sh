#module purge
#conda activate ghj_pyatb
export LD_PRELOAD=/mnt/sg001/opt/intel/oneapi2024/mkl/2024.0/lib/libmkl_avx512.so.2
#export OMP_NUM_THREADS=20

mpirun -np 1 python get_diel.py
