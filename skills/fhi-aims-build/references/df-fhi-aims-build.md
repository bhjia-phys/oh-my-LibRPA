# DF FHI-Aims Build Reference

Use this reference when repairing or reproducing the validated FHI-aims build on `df_iopcas_ghj`.

## Validated tree

- source: `/data/home/df_iopcas_ghj/app/FHIaims-master`
- build: `/data/home/df_iopcas_ghj/app/FHIaims-master/build`
- validated output binary:
  - `/data/home/df_iopcas_ghj/app/FHIaims-master/build/aims.260331.scalapack.mpi.x`

## Failure chain that was observed

The original configure failure was:

```text
The ELSI submodule is not downloaded! GIT_SUBMODULE was turned off or failed.
Please update submodules and try again.
```

The root-cause evidence was:

- the source tree was not a real git repository:
  - `.gitmodules` existed
  - `.git` did not
- `external_libraries/elsi_interface/` existed only as an empty directory
- therefore `GIT_SUBMODULE=ON` could never initialize ELSI automatically
- the cache file still assumed an older Intel environment:
  - `CMAKE_Fortran_COMPILER "mpif90"`
  - `CMAKE_C_COMPILER "icc"`
  - `CMAKE_CXX_COMPILER "icpc"`
  - `LIB_PATHS "/opt/intel/mkl/lib/intel64"`
- on this host, `mpif90 -show` resolved to `gfortran`, so Intel-specific Fortran flags failed immediately
- `icc` and `icpc` were no longer valid compiler names on this host
- `/opt/intel/mkl/lib/intel64` did not exist

## Verified repair

### 1. Populate vendored ELSI manually

Because the tree was not a full git clone, the working repair was to populate `elsi_interface` directly:

```bash
cd /data/home/df_iopcas_ghj/app/FHIaims-master/external_libraries
rm -rf elsi_interface
git clone https://gitlab.com/elsi_project/elsi_interface.git elsi_interface
```

Validated commit during recovery:

```text
fb5767923fbbbd336e700e882e782c4d0ac02a2d
```

### 2. Update the cache to the active oneAPI toolchain

The validated compiler triplet on `df` was:

- `mpiifort`
- `icx`
- `icpx`

The validated MKL root was:

- `/data/app/intel/oneapi-2024.2/mkl/2024.2/lib`

The working cache edits were:

- `CMAKE_Fortran_COMPILER "mpiifort"`
- `CMAKE_C_COMPILER "icx"`
- `CMAKE_CXX_COMPILER "icpx"`
- keep Intel Fortran flags
- remove `-ip` from `CMAKE_C_FLAGS`
- remove `-ip` from `CMAKE_CXX_FLAGS`
- set `LIB_PATHS "/data/app/intel/oneapi-2024.2/mkl/2024.2/lib"`

### 3. Reconfigure from a clean build state

```bash
cd /data/home/df_iopcas_ghj/app/FHIaims-master/build
rm -rf CMakeCache.txt CMakeFiles
cmake -C ../initial_cache.example.cmake ..
```

### 4. Rebuild

```bash
cd /data/home/df_iopcas_ghj/app/FHIaims-master/build
make -j4
```

## Practical checks that mattered

- always run `mpif90 -show` before trusting Intel-flavored cache flags
- always verify whether `elsi_interface/CMakeLists.txt` exists before retrying `cmake`
- if the tree is a copied snapshot rather than a git worktree, do not expect `GIT_SUBMODULE=ON` to help
- if the cache mentions `icc`, `icpc`, or `/opt/intel/...`, treat those as suspicious immediately on this host

## Logs captured during the validated recovery

- configure log:
  - `/data/home/df_iopcas_ghj/app/FHIaims-master/build/cmake.reconfigure.log`
- build log:
  - `/data/home/df_iopcas_ghj/app/FHIaims-master/build/make.j4.log`
