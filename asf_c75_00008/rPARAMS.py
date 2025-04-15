
"""
This is the script that captures all the key run parameters and is imported by GoGoNEMO.py
"""

rP_OCEANCORES='1024'
rP_STOCKDIR='/work/n02/n02/chbull/nemo/nemo_output'
rP_WORKDIR='/work/n02/n02/chbull/nemo/run/asf_c75_00008'
rP_RBUILD_NEMO='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/tools/REBUILD_NEMO/rebuild_nemo'
rP_MKPSI='/work/n02/n02/chbull/nemo/bld_configs/input_ajtoy/ncj_psi/post_grid_UV'
rP_PROJ='n02-PROPHET'
rP_CONFIG='asf_c75'
rP_CASE='00008'
rP_DESC='config 08. cases 73-97 trying tanh shelf with a range of open and blocked single width walls, tanh bathymetry is otherwise the same as c16. re-entrant zonal boundary, now with momentum diagnostics output. And improved world ocean atlas initial conditions and restoring as well as better vertical levels, this includes surface restoring in upper 10m. now with thickness weighted momentum diagnostics. This is the re-runs in light of paper revision with gm (2000) and eddy heat transport diagnostics. 100 year run'
rP_NDAYS='365'
rP_YEAR0='1'
rP_YEAR_MAX='100'

if __name__ == '__main__':
    print('This script is designed to be imported...')
