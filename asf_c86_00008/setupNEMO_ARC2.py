#!/usr/bin/env python 
#   Author: Christopher Bull. 
#   Affiliation:  Department of Geography and Environmental Sciences, 
#                 Northumbria University, Newcastle upon Tyne, UK
#   Contact: christopher.bull@northumbria.ac.uk
#   Date created: Mon, 15 Feb 2021 09:43:25
#   Machine created on: SB2Vbox
#
#   Update (15/02/2021): modified to work on ARCHER2 with nemo3.6 STABLE 
"""
 This is the script to set-up NEMO runs
"""
import sys,os
import datetime
import contextlib as ctx
import shutil
import glob
import subprocess
import f90nml
import numpy as np

class bcolors:
    """
    stolen: https://stackoverflow.com/questions/287871/how-to-print-colored-text-in-python
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def mkdir(p):
    """make directory of path that is passed"""
    try:
       os.makedirs(p)
       print("output folder: "+p+ " does not exist, we will make one.")
    except OSError as exc: # Python >2.5
       import errno
       if exc.errno == errno.EEXIST and os.path.isdir(p):
          pass
       else: raise

def mkdomcfg(rP_WORKDIR,workfol,DOMAINcfg,BFILE,rP_nml_patch,killisf):
    """function to do leg work for making domain_cfg.nc
    """
    os.mkdir(rP_WORKDIR+'/domaincfg/')
    os.chdir(rP_WORKDIR+'/domaincfg/')
    wdir=workfol+'domaincfg/'

    ifiles=sorted(glob.glob(wdir+'*'))
    assert(ifiles!=[]),"glob didn't find anything!"
    for f in ifiles:
        if os.path.isfile(f):
            shutil.copy2(f,rP_WORKDIR+'/domaincfg/'+os.path.basename(f))

    os.symlink(DOMAINcfg, 'make_domain_cfg.exe')
    if not killisf:
        os.symlink(BFILE, 'isf_draft_meter.nc')
        os.symlink(BFILE, 'bathy_meter.nc')
    else:
        shutil.copy2(BFILE,rP_WORKDIR+'/domaincfg/bathy_meter_template.nc')
        subprocess.call('module load nco;ncks -x -v isf_draft bathy_meter_template.nc bathy_meter_middle.nc;ncrename -v Bathymetry_isf,Bathymetry bathy_meter_middle.nc bathy_meter.nc;',shell=True)
        if os.path.exists(rP_WORKDIR+'/domaincfg/bathy_meter.nc'):
            print("We have sucessfully killed the ice-shelf!") 
        else:
            print("We have not sucessfully killed the ice-shelf!") 
            import pdb;pdb.set_trace()
        os.remove(rP_WORKDIR+'/domaincfg/bathy_meter_middle.nc')
        os.remove(rP_WORKDIR+'/domaincfg/bathy_meter_template.nc')

    #need bathymetry and isf file

    if rP_nml_patch is not None:
        nmlpath=rP_WORKDIR+'/domaincfg/namelist_cfg'
        assert(os.path.exists(nmlpath)),"can't find domaincfg/namelist_cfg"
        print(bcolors.HEADER+ "WARNING: "+bcolors.ENDC   +'We are patching the DOMAINCFG namelist '+nmlpath+' with: '+  bcolors.HEADER +str(rP_nml_patch) +bcolors.ENDC)
        f90nml.patch(nmlpath, rP_nml_patch, out_path=nmlpath+'_new')
        shutil.move(nmlpath+'_new', nmlpath)


def mkmesh(workfol,rP_WORKDIR,DOMAINcfg,BFILE,rP_nml_patch=None,killisf=False,extdomaincfg=['','']):
    """NEMO 4 in some cases, needs you to make a domain_cfg.nc file

    Note to make the namelist_cfg that worked for NEMO 4.0.4 we had to, hacking from:
        /mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/nemo_output/aj_ts_melt_off_dynlin_014/0001/namelist.0001
        -change jp_cfg into an integer
        -remove various elements from namrun
        -remove a few things from namdom (everything between rn_rdt and ln_crs)
        -added ln_teos10    = .true.
    
    :DOMAINcfg: executable to use
    :extdomaincfg: 3 options
        ['',''] - default, we will use parameters provided or modified via namelist (alone)
        ['hacked','/PATH/TO/pythonscripttohack_domain_cfg.nc'] - uses default but will additionally hack the domain_cfg.nc output using passed file
        ['rogue','/PATH/TO/domain_cfg.nc'] - total rogue, i.e., if you'd rather use an externally provided domaincfg (made elsewhere).
    :returns: @todo
    """
    if extdomaincfg[0]=='':
        mkdomcfg(rP_WORKDIR,workfol,DOMAINcfg,BFILE,rP_nml_patch,killisf)
    elif extdomaincfg[0]=='hacked':
        mkdomcfg(rP_WORKDIR,workfol,DOMAINcfg,BFILE,rP_nml_patch,killisf)
        print(bcolors.HEADER+ "WARNING: "+bcolors.ENDC   +'We are going to hack the domaincfg, using '+os.path.dirname(extdomaincfg[1])+'/'+bcolors.HEADER+os.path.basename(extdomaincfg[1])+ bcolors.ENDC)
    elif extdomaincfg[0]=='rogue':
        assert(os.path.exists(extdomaincfg[1])),"domain_cfg passed does not exist!" + extdomaincfg[1]
        #shutil.copy2(extdomaincfg[1],rP_WORKDIR+'/domain_cfg.nc')
        os.symlink(extdomaincfg[1], rP_WORKDIR+'/domain_cfg.nc')
        print(bcolors.HEADER+ "WARNING: "+bcolors.ENDC   +'We are using an externally provided domaincfg '+os.path.dirname(extdomaincfg[1])+'/'+bcolors.HEADER+os.path.basename(extdomaincfg[1])+ bcolors.ENDC)
    else:
        pass
        print(bcolors.WARNING + "ERROR: "  +'Do not know what to do with your passed argument for extdomaincfg'+  bcolors.ENDC )
        import pdb;pdb.set_trace()

    return



def main(workfol,rP_CONFIG,rP_CONFIG_TYPE,rP_CASE,NEMOexe,WCONFIG,BFILE,TSFILE,rP_nml_patch=None,FLXFCE='',extdomaincfg=['','']):
    """@todo: Docstring for main
    
    :DOMAINcfg: executable to use
    :extdomaincfg: 3 options
        ['',''] - default, we will use parameters provided or modified via namelist (alone)
        ['hacked','/PATH/TO/pythonscripttohack_domain_cfg.nc'] - uses default but will additionally hack the domain_cfg.nc output using passed file
        ['rogue','/PATH/TO/domain_cfg.nc'] - total rogue, i.e., if you'd rather use an externally provided domaincfg (made elsewhere).
    :returns: @todo
    """
    # check here that the symlinks exist
    print("Check forcing files exist..")
    assert(os.path.exists(BFILE)),"can't find file: "+BFILE
    assert(os.path.exists(TSFILE)),"can't find file: "+TSFILE
    assert(os.path.exists(NEMOexe)),"can't find file: "+NEMOexe
    print(".. Forcing files exist!")

    # for f-plane with regular grid spacing (and default depth levels)
    #rP_nml_patch={}
    #rP_nml_patch['namdom']={'jphgr_msh':2,'ppglam0' :0.0,'ppe1_deg':999999.0,'ppe2_deg':999999.0,'ppe1_m':10000.0,'ppe2_m':10000.0}

    # for f-plane with regular grid spacing *and* regular depth levels
    # uniform vertical (and uniform hoz)
    # probably has redundant elements
    #rP_nml_patch={}
    #rP_nml_patch['namdom']={'jphgr_msh':3,'ppglam0':0.0,'ppgphi0':-75.0,'ppe1_deg':999999.0,'ppe2_deg':999999.0,'ppe1_m':7857.742023485458,'ppe2_m':7857.742023485458,'ppsur':999999.0,'ppa0':999999.0,'ppa1':999999.0,'ppkth':0.0,'ppdzmin':20.,'pphmax':873.46602361,'ldbletanh':False,'ppa2':999999.0,'ppkth2':999999.0,'ppacr2':999999.0}

    # uniform vertical only (on Mercator grid)
    #rP_nml_patch={}
    #does work but perhaps has redundant elements..
    #rP_nml_patch['namdom']={'ppsur':999999.0,'ppa0':999999.0,'ppa1':999999.0,'ppkth':0.0,'ppdzmin':20.,'pphmax':720.,'ldbletanh':False,'ppa2':999999.0,'ppkth2':999999.0,'ppacr2':999999.0}

    #for a linear EOS
    #rP_nml_patch={}
    #rP_nml_patch['nameos']={'nn_eos': 2, 'rn_a0': 0.038356948, 'rn_b0': 0.805876093, 'rn_lambda1': 0.0000000, 'rn_lambda2': 0.0000000, 'rn_mu1': 0.0000000, 'rn_mu2': 0.0000000, 'rn_nu': 0.0000000}
    #rP_nml_patch['namdom']={'jphgr_msh':3,'ppglam0':0.0,'ppgphi0':-75.0,'ppe1_deg':999999.0,'ppe2_deg':999999.0,'ppe1_m':7857.742023485458,'ppe2_m':7857.742023485458,'ppsur':999999.0,'ppa0':999999.0,'ppa1':999999.0,'ppkth':0.0,'ppdzmin':20.,'pphmax':1100.46602361,'ldbletanh':False,'ppa2':999999.0,'ppkth2':999999.0,'ppacr2':999999.0}


    RDIR="/work/n02/n02/chbull/nemo/run"
    rP_WORKDIR=RDIR+'/'+rP_CONFIG+'_'+rP_CASE

    rP_PROJ='n02-PROPHET'

    rP_OCEANCORES=20
    if rP_CONFIG_TYPE=="ASF":
        rP_OCEANCORES=1024

    #avoid weird char'
    ## dodgy hack for desc
    #import xarray as xr
    #ifile=xr.open_dataset(FLXFCE[:-3]+'T.nc')
    #rP_DESC=ifile.attrs['experiment'] + '. Now with ice shelf turned off'
    #rP_DESC=ifile.attrs['experiment'] 

    #rP_DESC='cases 50-52 new runs with seasonl cycle variability (with improved sinx method of creating offsets), see meeting recording with adrian 09.07.2021. '+ifile.attrs['ename']

    #rP_DESC='case 57 new runs with c02_flat_isfuni (c16) bathymetry and forcing but with closed boundary condition (jperio 0)'
    #rP_DESC='cases 58-63 just trying out different shifts of the sea floor geometry north south but now wish ice-shelf off, tanh bathymetry is otherwise the same as asf_c32-37'
    #rP_DESC='cases 73-77 trying tanh shelf with single width full height wall new_bathy_ASF_c28_killisf.nc, tanh bathymetry is otherwise the same as c16 no isf. re-entrant zonal boundary'
    #rP_DESC='cases 78-82 trying tanh shelf with single width half height wall new_bathy_ASF_c29_killisf.nc, tanh bathymetry is otherwise the same as c16 no isf. re-entrant zonal boundary'
    #rP_DESC='cases 83-87 trying tanh shelf with single width almost full height wall new_bathy_ASF_c30_killisf.nc, tanh bathymetry is otherwise the same as c16 no isf. re-entrant zonal boundary'
    rP_DESC='cases 88-92 trying tanh shelf with single width blocking the shelf height wall new_bathy_ASF_c31_killisf.nc, tanh bathymetry is otherwise the same as c16 no isf. re-entrant zonal boundary'

    #rP_DESC='new set of tests for Sebastian with 20 year run, here with new yearly output'
    rP_DESC='AJTOY run using NEMO 4.0.4 on ARCHER2, sloped bathymetry but with re-entrant bdy'
    rP_DESC='AJTOY run using NEMO 4.0.4 on ARCHER2, but with sloped forcing and FLAT bottom'
    #rP_DESC='AJTOYinspired ISOMIP run using NEMO 4.0.4 on ARCHER2'
    rP_DESC='AJTOY run using NEMO 4.0.4 on ARCHER2, re-running but now with the sloped forcing and bathymetry changes suggested by Adrian on 09 12'

    rP_DESC='cases 73-117 trying tanh shelf with a range of open and blocked single width walls, tanh bathymetry is otherwise the same as c16 no isf. re-entrant zonal boundary, now with momentum diagnostics output'
    rP_DESC='cases 73-117 trying tanh shelf with a range of open and blocked single width walls, tanh bathymetry is otherwise the same as c16, now with isf. re-entrant zonal boundary, now with momentum diagnostics output. And improved world ocean atlas initial conditions and restoring as well as better vertical levels, this includes surface restoring in upper 10m. 90 years of spin up output followed by 10 of full output, now with thickness weighted momentum diagnostics. This is the re-run in light of the annoying issue with c89'

    #update: 6/2/24 new bathymetries for re-runs for paper revision
    rP_DESC='config 08. cases 73-97 trying tanh shelf with a range of open and blocked single width walls, tanh bathymetry is otherwise the same as c16. re-entrant zonal boundary, now with momentum diagnostics output. And improved world ocean atlas initial conditions and restoring as well as better vertical levels, this includes surface restoring in upper 10m. now with thickness weighted momentum diagnostics. This is the re-runs in light of paper revision with gm (2000) and eddy heat transport diagnostics. 100 year run'

    rP_YEAR0=1
    rP_YEAR_MAX=21
    rP_YEAR_MAX=351
    rP_YEAR_MAX=20
    rP_YEAR_MAX=60
    rP_YEAR_MAX=30
    rP_YEAR_MAX=370
    rP_YEAR_MAX=100
    #rP_YEAR_MAX=2
    #rP_YEAR_MAX=5
    #rP_YEAR_MAX=3

    #rP_STOCKDIR="/nerc/n02/n02/chbull/RawData/NEMO"  #- restart and output directory on rdf
    rP_STOCKDIR="/work/n02/n02/chbull/nemo/nemo_output" #- restart and output directory; now that rdf is offline

    #WCONFIG=/work/n02/n02/chbull/nemo/bld_configs/input_MISOMIP/NEMO_TYP
    #WCONFIG='/work/n02/n02/chbull/nemo/bld_configs/input_ajtoy'

    FORCING='/work/n01/shared/core2'

    #if rP_nml_patch!={}:
        #print("")
        #print(bcolors.HEADER+ "WARNING: "  +'We are patching the namelist with: '+  bcolors.ENDC +str(rP_nml_patch) )
        #print("")

    #make sure you've compiled this!
    #rP_RBUILD_NEMO=NEMOdir+'/TOOLS/REBUILD_NEMO/rebuild_nemo'
    rP_RBUILD_NEMO='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/tools/REBUILD_NEMO/rebuild_nemo'
    rP_MKPSI='/work/n02/n02/chbull/nemo/bld_configs/input_ajtoy/ncj_psi/post_grid_UV'

    DATE=str(datetime.datetime.now())

    ##-- User's choices END

    ##############################################
    ##-- initializations

    print("****************************************************")
    print("*          NEMO SIMULATION                         " )
    print("*   project      "+rP_PROJ                              )
    print("*   config       "+rP_CONFIG                          )
    print("*   config_type  "+bcolors.WARNING+rP_CONFIG_TYPE                     +bcolors.ENDC  )
    print("*   NEMOexe      "+NEMOexe                           )
    print("*   wconfig      "+WCONFIG                           )
    print("*   case         "+bcolors.WARNING+rP_CASE                            +bcolors.ENDC  )
    print("*   desc         "+rP_DESC                              )
    print("****************************************************")

    #############################################################
    ###-- prepare run dir

    print( "  ")
    print( "NOTE: we are using wconfig:"+WCONFIG)
    print( "  ")

    ##create run folder
    if os.path.exists(rP_WORKDIR):
        print(bcolors.FAIL+"WARNING: "+rP_WORKDIR+" already exists, so we will STOP"+bcolors.ENDC  )
        sys.exit("")
    else:
        print("WARNING: "+rP_WORKDIR+" does not exist , so we will try "+bcolors.WARNING+"CREATE"+bcolors.ENDC +' it.' )
        os.mkdir(rP_WORKDIR)
        os.chdir(rP_WORKDIR)

        with ctx.closing(open(rP_WORKDIR+'/README','w')) as handle:
            handle.write('*****************************************************'+"\n")
            handle.write('*          NEMO SIMULATION                          *'+"\n")
            handle.write('*   project   '+rP_PROJ            +'                     *'+"\n")
            handle.write('*   config    '+rP_CONFIG          +'                     *'+"\n")
            handle.write('*   NEMOexe   '+NEMOexe         +'                     *'+"\n")
            handle.write('*   case      '+rP_CASE            +'                     *'+"\n")
            handle.write('*   Desc      '+rP_DESC            +'                     *'+"\n")
            handle.write('*   Date      '+DATE            +'                     *'+"\n")
            handle.write('*                                                   *'+"\n")
            handle.write('*   Users choices:                                 *'+"\n")
            handle.write('*   rP_PROJ        '+rP_PROJ        + '                      *'+"\n")
            handle.write('*   rP_CONFIG      '+rP_CONFIG      + '                      *'+"\n")
            handle.write('*   rP_CONFIG_TYPE '+rP_CONFIG_TYPE + '                      *'+"\n")
            handle.write('*   BFILE       '+BFILE       + '                      *'+'\n')
            handle.write('*   TSFILE      '+TSFILE      + '                      *'+'\n')
            if FLXFCE!='':
                handle.write('*   FLXFILE      '+FLXFCE      + '                      *'+'\n')
                #handle.write('*   ENAME      '+ifile.attrs['ename']      + '                      *'+'\n')
            handle.write('*   rP_CASE        '+rP_CASE        + '                      *'+'\n')
            handle.write('*   rP_YEAR0       '+str(rP_YEAR0)      + '                      *'+'\n')
            handle.write('*   rP_YEAR_MAX    '+str(rP_YEAR_MAX)   + '                      *'+'\n')
            handle.write('*   RDIR        '+RDIR        + '                      *'+'\n')
            handle.write('*   rP_WORKDIR     '+rP_WORKDIR     + '                      *'+'\n')
            handle.write('*   rP_STOCKDIR    '+rP_STOCKDIR    + '                      *'+'\n')
            handle.write('*   rP_CONFIG     '+rP_CONFIG     + '                      *'+'\n')
            handle.write('*   FORCING     '+FORCING     + '                      *'+'\n')
            handle.write('*   NEMOdir     '+NEMOdir     + '                      *'+'\n')
            handle.write('*****************************************************'+'\n')

        #cat << EOF > ./env_rec
        with ctx.closing(open(rP_WORKDIR+'/env_rec','w')) as handle:
            handle.write('*   Date      '+DATE            +'*'+"\n")
            handle.write('*   record of current env:      '+"\n")
            ENV= os.getenv('ENV')
            handle.write(str(ENV)+"\n")
            handle.write(''+"\n")
            handle.write('*   record of current path:      '+"\n")
            ENV= os.getenv('PATH')
            handle.write(ENV+"\n")


        #nemo and xios
        #os.symlink(src, dst)
        os.symlink(NEMOexe, 'nemo.exe')

        #ln -s /work/n02/n02/chbull/nemo/models/XIOSv1/bin/xios_server.exe 
        #os.symlink('/work/n02/n02/chbull/nemo/models/XIOSv1_arc2/bin/xios_server.exe', 'xios_server.exe')

        ##cp template: namelists, *.xml etc
        # Copy src to dst. (cp src dst)
        # see pro/cons at 
        # https://stackoverflow.com/questions/123198/how-do-i-copy-a-file-in-python
        #ifiles=sorted(glob.glob('/home/chris/VBoxSHARED/repos/nemo_wed_analysis/ajtoy/configs/rnemoARCHER/*'))
        ifiles=sorted(glob.glob(workfol+'*'))
        assert(ifiles!=[]),"glob didn't find anything!"
        for f in ifiles:
            if os.path.isfile(f):
                shutil.copy2(f,rP_WORKDIR+'/')

        if rP_CONFIG_TYPE=="AJTOY":
            shutil.move(rP_WORKDIR+'/'+'namelist_ref_ajtoy',rP_WORKDIR+'/'+'namelist_ref')
            print(bcolors.WARNING + "WARNING: Using namelist_ref_ajtoy" + bcolors.ENDC)
        elif rP_CONFIG_TYPE=="ASF":
            shutil.move(rP_WORKDIR+'/'+'namelist_ref_asf',rP_WORKDIR+'/'+'namelist_ref')
            print(bcolors.WARNING + "WARNING: Using namelist_ref_asf" + bcolors.ENDC)

            #print(bcolors.WARNING + "WARNING: Using xml file and field defs that will output namdyntrd" + bcolors.ENDC)
            #shutil.move(rP_WORKDIR+'/'+'file_def_nemo-oce_asfmo.xml',rP_WORKDIR+'/'+'file_def_nemo-oce.xml')
            #shutil.move(rP_WORKDIR+'/'+'field_def_nemo-oce_asfmo.xml',rP_WORKDIR+'/'+'field_def_nemo-oce.xml')

            print(bcolors.WARNING + "WARNING: Using xml file and field defs that will output spin up diogs" + bcolors.ENDC)
            shutil.move(rP_WORKDIR+'/'+'file_def_nemo-oce_spin.xml',rP_WORKDIR+'/'+'file_def_nemo-oce.xml')

            os.mkdir(rP_WORKDIR+'/flxfce/')
            if FLXFCE!='':
                print()
                print(bcolors.WARNING + "WARNING: Using flxfce " +  FLXFCE + bcolors.ENDC)
                print()
                assert(os.path.exists(FLXFCE[:-3]+'T.nc')),"can't find flux forcing grid_T file: "+FLXFCE[:-3]+'T.nc'
                assert(os.path.exists(FLXFCE[:-3]+'U.nc')),"can't find flux forcing grid_T file: "+FLXFCE[:-3]+'U.nc'
                assert(os.path.exists(FLXFCE[:-3]+'V.nc')),"can't find flux forcing grid_T file: "+FLXFCE[:-3]+'V.nc'

                for yy in np.arange(rP_YEAR0,rP_YEAR_MAX+52):
                    yy=str(yy).zfill(4)+'.nc'
                    os.symlink(FLXFCE[:-3]+'T.nc', rP_WORKDIR+'/flxfce/flxforce_grid_T_y'+yy)
                    os.symlink(FLXFCE[:-3]+'U.nc', rP_WORKDIR+'/flxfce/flxforce_grid_U_y'+yy)
                    os.symlink(FLXFCE[:-3]+'V.nc', rP_WORKDIR+'/flxfce/flxforce_grid_V_y'+yy)
        else:
            os.remove(rP_WORKDIR+'/'+'namelist_ref_ajtoy')

        if rP_nml_patch is not None:
            nmlpath=rP_WORKDIR+'/namelist_ref'
            assert(os.path.exists(nmlpath)),"can't find namelist_ref"
            print(bcolors.HEADER+ "WARNING: "+bcolors.ENDC   +'We are patching the main NEMO namelist '+nmlpath+' with: '+  bcolors.HEADER +str(rP_nml_patch) +bcolors.ENDC + " (this shortly gets copied to be namelist_cfg, which then gets patched by preNEMO.py ...)")
            f90nml.patch(nmlpath, rP_nml_patch, out_path=nmlpath+'_new')
            shutil.move(nmlpath+'_new', nmlpath)

        #os.symlink('namelist_ref', 'namelist_cfg')
        #NEMO4 doesn't seem to like this! (symlink)
         #STOP
           #===>>>> : bad opening file: namelist_cfg

        shutil.copy2(rP_WORKDIR+'/'+'namelist_ref',rP_WORKDIR+'/'+'namelist_cfg')

        print(bcolors.WARNING + "WARNING: Using bathymetry and ice-shelf draft" + bcolors.ENDC+" from: "+BFILE)
        print("WARNING: ")

        os.symlink(BFILE, 'isf_draft_meter.nc')
        os.symlink(BFILE, 'bathy_meter.nc')

        print("WARNING: ")
        print(bcolors.WARNING + "WARNING: Using restoring and non-standard temp init"+ bcolors.ENDC+": "+TSFILE)
        os.symlink(TSFILE, 'TS_init.nc')
        os.symlink(TSFILE, 'resto.nc')
        print("WARNING: ")


        #ln -s /work/n02/n02/chbull/nemo/bld_configs/input_MISOMIP/NEMO_TYP/nemo_base_WARM-NEWFIX.nc TS_init.nc

    #file that will be imported by GoGoNEMO.py for all run parameters
    with ctx.closing(open(rP_WORKDIR+'/rPARAMS.py','w')) as handle:
            handle.write(''+'\n')

            handle.write('"""'+'\n')
            handle.write("This is the script that captures all the key run parameters and is imported by GoGoNEMO.py"+"\n")
            handle.write('"""'+'\n')
            handle.write(''+'\n')

            handle.write("rP_OCEANCORES='"  +str(rP_OCEANCORES)+"'"+'\n')
            handle.write("rP_STOCKDIR='"  +str(rP_STOCKDIR)+"'"+'\n')
            handle.write("rP_WORKDIR='"  +str(rP_WORKDIR)+"'"+'\n')
            handle.write("rP_RBUILD_NEMO='"  +str(rP_RBUILD_NEMO)+"'"+'\n')
            handle.write("rP_MKPSI='"  +str(rP_MKPSI)+"'"+'\n')
            handle.write("rP_PROJ='"  +str(rP_PROJ)+"'"+'\n')
            handle.write("rP_CONFIG='"  +str(rP_CONFIG)+"'"+'\n')
            handle.write("rP_CASE='"  +str(rP_CASE)+"'"+'\n')
            handle.write("rP_DESC='"  +str(rP_DESC)+"'"+'\n')
            handle.write("rP_NDAYS='"  +str(rP_NDAYS)+"'"+'\n')
            handle.write("rP_YEAR0='"  +str(rP_YEAR0)+"'"+'\n')
            handle.write("rP_YEAR_MAX='"  +str(rP_YEAR_MAX)+"'"+'\n')

            #handle.write("rP_nml_patch="  +str(rP_nml_patch)+" "+'\n')

            handle.write(''+'\n')
            handle.write("if __name__ == '__main__':" +"\n")
            handle.write("    print('This script is designed to be imported...')"+"\n")


    with ctx.closing(open(rP_WORKDIR+'/goNEMOquick.sh','w')) as handle:
        handle.write('#!/bin/bash'+'\n')
        handle.write('#SBATCH --qos=short'+'\n')
        handle.write('#SBATCH --job-name=nemo_test'+'\n')
        handle.write('#SBATCH --time=00:20:00'+'\n')
        if rP_CONFIG_TYPE=="ASF":
            handle.write('#SBATCH --nodes=8'+'\n')
        else:
            handle.write('#SBATCH --nodes=1'+'\n')

        handle.write('#SBATCH --ntasks='+str(rP_OCEANCORES)+'\n')
        handle.write('#SBATCH --account=n02-PROPHET'+'\n')
        handle.write('#SBATCH --partition=standard'+'\n')
        handle.write('module restore'+"\n")
        handle.write('module load cray-hdf5-parallel'+"\n")
        handle.write('module load cray-netcdf-hdf5parallel'+"\n")
        handle.write('module load xpmem'+"\n")
        handle.write('module load perftools-base'+"\n")
        handle.write('export OMP_NUM_THREADS=1'+'\n')
        handle.write('export PYTHONPATH=/work/n02/n02/chbull/anaconda3/pkgs;export PATH=/work/n02/n02/chbull/anaconda3/bin:$PATH;source activate root'+'\n')
        handle.write('#'+'\n')
        handle.write("#This is the script allows you to run NEMO real quick..."+"\n")
        handle.write(''+'\n')

        if extdomaincfg[0]=='' or extdomaincfg[0]=='hacked':
            handle.write('#create domain_cfg.nc'+'\n')
            handle.write('cd '+'domaincfg'+"\n")
            handle.write('srun -n 1 ./make_domain_cfg.exe '+"\n")
            handle.write("if [ -f domain_cfg.nc ]; then"+"\n")
            handle.write('   mv domain_cfg.nc ../'+"\n")
            handle.write('else'+"\n")
            handle.write('   echo "ERROR: domain_cfg NOT created, stopping."'+"\n")
            handle.write('   exit 1'+"\n")
            handle.write("fi"+"\n")
            handle.write('cd '+'..'+"\n")
            handle.write(''+'\n')
            if extdomaincfg[0]=='hacked':
                handle.write('echo "Current Date and Time is (for domaincfg hacking timer): " '+'`date`'+"\n")
                handle.write('python ' +extdomaincfg[1] +' '+rP_WORKDIR+'/domain_cfg.nc '+rP_WORKDIR+'/domain_cfg_hckd.nc '+'\n')
                handle.write("if [ -f domain_cfg_hckd.nc ]; then"+"\n")
                handle.write('   echo "YAY: hacked domain_cfg created."'+"\n")
                handle.write('   rm domain_cfg.nc'+"\n")
                handle.write('   mv domain_cfg_hckd.nc domain_cfg.nc'+"\n")
                handle.write('else'+"\n")
                handle.write('   echo "ERROR: hacked domain_cfg NOT created, stopping."'+"\n")
                handle.write('   exit 1'+"\n")
                handle.write("fi"+"\n")
                handle.write('echo "Current Date and Time is (for domaincfg hacking timer): " '+'`date`'+"\n")
                handle.write(''+"\n")

        handle.write('python preNEMO.py'+'\n')
        if rP_CONFIG_TYPE=="ASF":
            handle.write('srun --ntasks='+str(rP_OCEANCORES)+' ./nemo.exe'+'\n')
        else:
            handle.write('srun --ntasks='+str(rP_OCEANCORES)+' --mem-bind=local --cpu-bind=v,map_cpu:00,0x1,0x2,0x3,0x4,0x5,0x6,0x7,0x8,0x9,0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x20,0x21,0x22,0x23, ./nemo.exe'+'\n')
        handle.write('python postNEMO.py'+'\n')
        handle.write('#or more simply'+'\n')
        handle.write('#srun --distribution=block:block --hint=nomultithread -n 4 ./nemo.exe'+'\n')

        handle.write('#rebuild outputs '+'\n')
        handle.write('#/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/tools/REBUILD_NEMO/rebuild_nemo mesh_mask '+str(rP_OCEANCORES)+'\n')


    subprocess.call('chmod u+x '+rP_WORKDIR+'/goNEMOquick.sh',shell=True)

    with ctx.closing(open(rP_WORKDIR+'/goNEMOlong.sh','w')) as handle:
        handle.write('#!/bin/bash'+'\n')
        handle.write('#SBATCH --job-name='+rP_CONFIG+'_'+rP_CASE+'\n')
        #handle.write('#SBATCH --time=23:57:02'+'\n')
        handle.write('#SBATCH --time=47:57:02'+'\n')
        if rP_CONFIG_TYPE=="ASF":
            handle.write('#SBATCH --nodes=8'+'\n')
        else:
            handle.write('#SBATCH --nodes=1'+'\n')

        handle.write('#SBATCH --ntasks='+str(rP_OCEANCORES)+'\n')
        handle.write('#SBATCH --account=n02-PROPHET'+'\n')
        handle.write('#SBATCH --partition=standard'+'\n')
        #handle.write('#SBATCH --qos=standard'+'\n')
        handle.write('#SBATCH --qos=long'+'\n')
        handle.write('module restore'+"\n")
        handle.write('module load cray-hdf5-parallel'+"\n")
        handle.write('module load cray-netcdf-hdf5parallel'+"\n")
        handle.write('module load xpmem'+"\n")
        handle.write('module load perftools-base'+"\n")
        handle.write('export OMP_NUM_THREADS=1'+'\n')
        handle.write('export PYTHONPATH=/work/n02/n02/chbull/anaconda3/pkgs;export PATH=/work/n02/n02/chbull/anaconda3/bin:$PATH;source activate root'+'\n')
        handle.write('#'+'\n')
        handle.write("#This is the script allows you to run NEMO one job at a time..."+"\n")
        handle.write('echo "Current Date and Time is (start): " '+'`date`'+"\n")
        handle.write(''+'\n')

        if extdomaincfg[0]=='' or extdomaincfg[0]=='hacked':
            handle.write('#create domain_cfg.nc'+'\n')
            handle.write('cd '+'domaincfg'+"\n")
            handle.write('srun -n 1 ./make_domain_cfg.exe '+"\n")
            handle.write("if [ -f domain_cfg.nc ]; then"+"\n")
            handle.write('   mv domain_cfg.nc ../'+"\n")
            handle.write('else'+"\n")
            handle.write('   echo "ERROR: domain_cfg NOT created, stopping."'+"\n")
            handle.write('   exit 1'+"\n")
            handle.write("fi"+"\n")
            handle.write('cd '+'..'+"\n")
            handle.write(''+'\n')
            if extdomaincfg[0]=='hacked':
                handle.write('echo "Current Date and Time is (for domaincfg hacking timer): " '+'`date`'+"\n")
                handle.write('python ' +extdomaincfg[1] +' '+rP_WORKDIR+'/domain_cfg.nc '+rP_WORKDIR+'/domain_cfg_hckd.nc '+'\n')
                handle.write("if [ -f domain_cfg_hckd.nc ]; then"+"\n")
                handle.write('   echo "YAY: hacked domain_cfg created."'+"\n")
                handle.write('   rm domain_cfg.nc'+"\n")
                handle.write('   mv domain_cfg_hckd.nc domain_cfg.nc'+"\n")
                handle.write('else'+"\n")
                handle.write('   echo "ERROR: hacked domain_cfg NOT created, stopping."'+"\n")
                handle.write('   exit 1'+"\n")
                handle.write("fi"+"\n")
                handle.write('echo "Current Date and Time is (for domaincfg hacking timer): " '+'`date`'+"\n")
                handle.write(''+"\n")

        handle.write(' '+"\n")
        handle.write('cd $cwd'+"\n")
        handle.write("if [ -f time.year.step ]; then"+"\n")
        handle.write("   source time.year.step"+"\n")
        handle.write('else'+"\n")
        handle.write("   echo 'year=1' > time.year.step"+"\n")
        handle.write("   source time.year.step"+"\n")
        handle.write(' '+"\n")
        handle.write("fi"+"\n")
        handle.write('echo "Running year: "'+"\n")
        handle.write('echo "Running year: "$year" out of '+str(rP_YEAR_MAX)+'"'+"\n")
        handle.write('echo " "'+"\n")
        handle.write("while [ $year -lt "+str(int(rP_YEAR_MAX)+1)+" ]"+"\n")
        #handle.write('for i in {1..'+rP_YEAR_MAX+'}'+"\n")
        #handle.write('for i in {1..'+rP_YEAR_MAX+'}'+"\n")
        handle.write('do'+"\n")

        handle.write('    echo "Current Date and Time is ("$year" start): " '+'`date`'+"\n")
        handle.write('    echo "Run NEMO"'+"\n")

        handle.write('    cd '+rP_WORKDIR+"\n")
        handle.write('    echo "Current directory is:"'+"\n")
        handle.write('    pwd'+"\n")
        handle.write('    python preNEMO.py'+"\n")
        handle.write('    srun --ntasks='+str(rP_OCEANCORES)+' ./nemo.exe'+'\n')
        handle.write(' '+"\n")

        handle.write('    echo "Clean up NEMO"'+"\n")
        handle.write('    srun --ntasks='+'1'+' --tasks-per-node='+'1'+' --cpus-per-task=1 python postNEMO.py '+"\n")

        handle.write('    wait'+"\n")
        handle.write('    echo "Current Date and Time is ("$year" end): " '+'`date`'+"\n")

        handle.write('    '+"\n")

        handle.write('    echo "And repeat."'+"\n")

        handle.write("    year=$[$year+1]"+"\n")
        handle.write('    cd $cwd'+"\n")
        handle.write("    echo 'year='$year > time.year.step"+"\n")
        handle.write('done'+"\n")

        handle.write('echo "Current Date and Time is (end): " '+'`date`'+"\n")
        handle.write('echo "Its over..."'+"\n")

    subprocess.call('chmod u+x '+rP_WORKDIR+'/goNEMOlong.sh',shell=True)


    with ctx.closing(open(rP_WORKDIR+'/goNEMOproduction.sh','w')) as handle:
        handle.write('#!/bin/bash'+'\n')
        handle.write('#SBATCH --job-name='+rP_CONFIG+'_'+rP_CASE+'\n')
        handle.write('#SBATCH --time=23:57:02'+'\n')
        #handle.write('#SBATCH --time=47:57:02'+'\n')
        if rP_CONFIG_TYPE=="ASF":
            handle.write('#SBATCH --nodes=8'+'\n')
        else:
            handle.write('#SBATCH --nodes=1'+'\n')

        handle.write('#SBATCH --ntasks='+str(rP_OCEANCORES)+'\n')
        handle.write('#SBATCH --account=n02-PROPHET'+'\n')
        handle.write('#SBATCH --partition=standard'+'\n')
        #handle.write('#SBATCH --qos=long'+'\n')
        handle.write('#SBATCH --qos=standard'+'\n')
        handle.write('module restore'+"\n")
        handle.write('module load cray-hdf5-parallel'+"\n")
        handle.write('module load cray-netcdf-hdf5parallel'+"\n")
        handle.write('module load xpmem'+"\n")
        handle.write('module load perftools-base'+"\n")
        handle.write('export OMP_NUM_THREADS=1'+'\n')
        handle.write('export PYTHONPATH=/work/n02/n02/chbull/anaconda3/pkgs;export PATH=/work/n02/n02/chbull/anaconda3/bin:$PATH;source activate root'+'\n')
        handle.write('#'+'\n')
        handle.write("#This is the script allows you to run NEMO one job at a time..."+"\n")
        handle.write('echo "Current Date and Time is (start): " '+'`date`'+"\n")
        handle.write(''+'\n')

        if extdomaincfg[0]=='' or extdomaincfg[0]=='hacked':
            handle.write('#create domain_cfg.nc'+'\n')
            handle.write('cd '+'domaincfg'+"\n")
            handle.write('srun -n 1 ./make_domain_cfg.exe '+"\n")
            handle.write("if [ -f domain_cfg.nc ]; then"+"\n")
            handle.write('   mv domain_cfg.nc ../'+"\n")
            handle.write('else'+"\n")
            handle.write('   echo "ERROR: domain_cfg NOT created, stopping."'+"\n")
            handle.write('   exit 1'+"\n")
            handle.write("fi"+"\n")
            handle.write('cd '+'..'+"\n")
            handle.write(''+'\n')
            if extdomaincfg[0]=='hacked':
                handle.write('echo "Current Date and Time is (for domaincfg hacking timer): " '+'`date`'+"\n")
                handle.write('python ' +extdomaincfg[1] +' '+rP_WORKDIR+'/domain_cfg.nc '+rP_WORKDIR+'/domain_cfg_hckd.nc '+'\n')
                handle.write("if [ -f domain_cfg_hckd.nc ]; then"+"\n")
                handle.write('   echo "YAY: hacked domain_cfg created."'+"\n")
                handle.write('   rm domain_cfg.nc'+"\n")
                handle.write('   mv domain_cfg_hckd.nc domain_cfg.nc'+"\n")
                handle.write('else'+"\n")
                handle.write('   echo "ERROR: hacked domain_cfg NOT created, stopping."'+"\n")
                handle.write('   exit 1'+"\n")
                handle.write("fi"+"\n")
                handle.write('echo "Current Date and Time is (for domaincfg hacking timer): " '+'`date`'+"\n")
                handle.write(''+"\n")

        handle.write(' '+"\n")
        handle.write('cd $cwd'+"\n")
        handle.write("if [ -f time.year.step ]; then"+"\n")
        handle.write("   source time.year.step"+"\n")
        handle.write('else'+"\n")
        handle.write("   echo 'year=1' > time.year.step"+"\n")
        handle.write("   source time.year.step"+"\n")
        handle.write(' '+"\n")
        handle.write("fi"+"\n")

        handle.write('echo "---                ---"'+"\n")
        handle.write('echo "---  Phase 1 start ---"'+"\n")
        handle.write('echo "---     Spinup     ---"'+"\n")
        handle.write('echo "---                ---"'+"\n")

        handle.write('echo "Running year: "'+"\n")
        handle.write('echo "Running year: "$year" out of '+str(rP_YEAR_MAX)+'"'+"\n")
        handle.write('echo " "'+"\n")
        #this should be the number of spin up years you want, e.g., if rP_YEAR_MAX=20 and you have SYEARS=int(rP_YEAR_MAX)-4, then 20-5 (15!) will be spin up
        #SYEARS=int(rP_YEAR_MAX)-4
        #SYEARS=int(rP_YEAR_MAX)-19
        SYEARS=int(rP_YEAR_MAX)-9
        handle.write("while [ $year -lt "+str(SYEARS)+" ]"+"\n")
        handle.write('do'+"\n")

        handle.write('    echo "Current Date and Time is ("$year" start): " '+'`date`'+"\n")
        handle.write('    echo "Run NEMO"'+"\n")

        handle.write('    cd '+rP_WORKDIR+"\n")
        handle.write('    echo "Current directory is:"'+"\n")
        handle.write('    pwd'+"\n")
        handle.write('    python preNEMO.py'+"\n")
        handle.write('    srun --ntasks='+str(rP_OCEANCORES)+' ./nemo.exe'+'\n')
        handle.write(' '+"\n")

        handle.write('    echo "Clean up NEMO"'+"\n")
        handle.write('    srun --ntasks='+'1'+' --tasks-per-node='+'1'+' --cpus-per-task=1 python postNEMO.py '+"\n")

        handle.write('    wait'+"\n")
        handle.write('    echo "Current Date and Time is ("$year" end): " '+'`date`'+"\n")

        handle.write('    '+"\n")

        handle.write('    echo "And repeat."'+"\n")

        handle.write("    year=$[$year+1]"+"\n")
        handle.write('    cd $cwd'+"\n")
        handle.write("    echo 'year='$year > time.year.step"+"\n")
        handle.write('done'+"\n")

        handle.write('echo "---              ---"'+"\n")
        handle.write('echo "---  Phase 1 end ---"'+"\n")
        handle.write('echo "---              ---"'+"\n")
        handle.write('echo ""'+"\n")

        handle.write('echo "Swapping in production xml files"'+"\n")
        handle.write('#change outputs from spin up to ones with full output and momentum diagnostics'+'\n')
        handle.write('mv file_def_nemo-oce_asfmo.xml file_def_nemo-oce.xml'+"\n")
        handle.write('mv field_def_nemo-oce_asfmo.xml field_def_nemo-oce.xml'+"\n")
        handle.write('echo "Turning on momentum diagnostics"'+"\n")
        handle.write('#thanks Marshall!'+'\n')
        handle.write('f90nml -g namtrd -v ln_dyn_trd=True --patch '+rP_WORKDIR+'/'+'namelist_cfg '+rP_WORKDIR+'/'+'namelist_meh'+"\n")
        handle.write("if [ -f namelist_meh ]; then"+"\n")
        handle.write('   echo "YAY: namelist succesfully hacked."'+"\n")
        handle.write('else'+"\n")
        handle.write('   echo "ERROR: hacked namelist NOT created, stopping."'+"\n")
        handle.write('   exit 1'+"\n")
        handle.write(' '+"\n")
        handle.write("fi"+"\n")
        #we have to do namelist_ref b/c preNEMO copies over the cfg
        handle.write('mv '+rP_WORKDIR+'/'+'namelist_meh '+rP_WORKDIR+'/'+'namelist_ref '+"\n")
        

        handle.write('echo ""'+"\n")

        handle.write('echo "---                ---"'+"\n")
        handle.write('echo "---  Phase 2 start ---"'+"\n")
        handle.write('echo "---  USEFUL OUTPUT ---"'+"\n")

        handle.write("while [ $year -lt "+str(int(rP_YEAR_MAX)+1)+" ]"+"\n")
        handle.write('do'+"\n")

        handle.write('    echo "Current Date and Time is ("$year" start): " '+'`date`'+"\n")
        handle.write('    echo "Run NEMO"'+"\n")

        handle.write('    cd '+rP_WORKDIR+"\n")
        handle.write('    echo "Current directory is:"'+"\n")
        handle.write('    pwd'+"\n")
        handle.write('    python preNEMO.py'+"\n")
        handle.write('    srun --ntasks='+str(rP_OCEANCORES)+' ./nemo.exe'+'\n')
        handle.write(' '+"\n")

        handle.write('    echo "Clean up NEMO"'+"\n")
        handle.write('    srun --ntasks='+'1'+' --tasks-per-node='+'1'+' --cpus-per-task=1 python postNEMO.py '+"\n")

        handle.write('    wait'+"\n")
        handle.write('    echo "Current Date and Time is ("$year" end): " '+'`date`'+"\n")

        handle.write('    '+"\n")

        handle.write('    echo "And repeat."'+"\n")

        handle.write("    year=$[$year+1]"+"\n")
        handle.write('    cd $cwd'+"\n")
        handle.write("    echo 'year='$year > time.year.step"+"\n")
        handle.write('done'+"\n")

        handle.write('echo "---                ---"'+"\n")
        handle.write('echo "---  Phase 2 end   ---"'+"\n")
        handle.write('echo "---                ---"'+"\n")

        #add if statement here!
        #if [ $Server_Name -eq 1 ];then
        handle.write("if [ $year -eq "+str(int(rP_YEAR_MAX)+1)+" ]; then"+"\n")
        handle.write("   echo 'Sweet, we have finished the run side of things now to do post proc'"+"\n")

        handle.write('   echo "---                      ---"'+"\n")
        handle.write('   echo "---  Post-proc start     ---"'+"\n")
        handle.write('   echo "Current Date and Time is (end): " '+'`date`'+"\n")
        handle.write('   echo ""'+"\n")
        handle.write('   echo "#activate anaconda (this needs python2)"'+"\n")
        handle.write('   export PYTHONPATH=/work/n02/n02/chbull/anaconda2/pkgs;export PATH=/work/n02/n02/chbull/anaconda2/bin:$PATH;source activate root'+"\n")

        #need to find mk_nemo_spinup.py
        #output folder - this doesn't exist yet!
        odir=rP_STOCKDIR+'/'+rP_CONFIG+'_'+rP_CASE+'/'
        supf=os.path.dirname(os.path.dirname(os.path.dirname(workfol)))+'/diagnostics/mk_nemo_spinup.py'
        assert(os.path.exists(supf)),"cannot find mk_nemo_spinup.py file"
        
        handle.write('   echo "run wrappers for spin up and ncra post proc"'+"\n")
        #crucial so that the wrappers are found in the 'right' place - does mean the pbs files will be here tho
        handle.write('   cd '+os.path.dirname(os.path.dirname(os.path.dirname(workfol)))+'/diagnostics/'+"\n")
        handle.write('   python ' + supf + ' ' + odir + ' ' + odir+"\n")

        handle.write('   echo "---  Post-proc end     ---"'+"\n")
        handle.write('   echo "---                    ---"'+"\n")

        handle.write('else'+"\n")
        handle.write("   echo 'E R R O R: something has gone wrong and we havent done the right amount of years to be here (doing post-proc of production output)..'"+"\n")
        handle.write('   echo "Current Date and Time is (end): " '+'`date`'+"\n")
        handle.write('   exit 1'+"\n")
        handle.write("fi"+"\n")

        handle.write('echo "Current Date and Time is (end): " '+'`date`'+"\n")
        handle.write('echo "Its over..."'+"\n")

    subprocess.call('chmod u+x '+rP_WORKDIR+'/goNEMOproduction.sh',shell=True)

    #so we can run lots at once
    mkdir(workfol+'rfiles/')
    if not os.path.exists(workfol+'rfiles/runme'):
        with ctx.closing(open(workfol+'rfiles/runme','w')) as handle:
            handle.write(str(rP_YEAR_MAX)+''+'\n')

    with ctx.closing(open(workfol+'rfiles/runme','a')) as handle:
        handle.write(rP_WORKDIR+'/ '+'\n')

    return rP_WORKDIR


if __name__ == "__main__":
    workfol='/work/n02/n02/chbull/repos/nemo_wed_analysis/ajtoy/configs/rnemoARCHER2/'
    
    IFX='-30'
    CASE='01'
    CASE='04'
    CASE='05'
    CASE='06'
    CASE='07'
    CASE='08'
    #CASE='s01'
    rP_CASE=CASE.zfill(5)

    rP_NDAYS=365
    rP_CONFIG_TYPE='SVM'
    #rP_CONFIG_TYPE='AJTOY'
    rP_CONFIG_TYPE='ASF'
    #rP_CONFIG_TYPE="SR_ML"
    mkillisf=False
    rP_nml_patch={}

    #for NUM,flx in zip([73,74,75,76,77],['18','19','01','20','21']):
    #for NUM,flx in zip([78,79,80,81,82],['18','19','01','20','21']):
    for NUM,flx in zip([83,84,85,86,87],['18','19','01','20','21']):
    #for NUM,flx in zip([88,89,90,91,92],['18','19','01','20','21']):
    #for NUM,flx in zip([93,94,95,96,97],['18','19','01','20','21']):

    #for NUM,flx in zip([93,94,95,96,97],['18','19','01','20','21']):
    #for NUM,flx in zip([98,99,100,101,102],['18','19','01','20','21']):
    #for NUM,flx in zip([103,104,105,106,107],['18','19','01','20','21']):
    #for NUM,flx in zip([108,109,110,111,112],['18','19','01','20','21']):
    #for NUM,flx in zip([113,114,115,116,117],['18','19','01','20','21']):

        if rP_CONFIG_TYPE=="SVM":
            WCONFIG='/work/n02/n02/chbull/nemo/bld_configs/input_ajtoy'
            #IFX='-66'
            #IFX='-30'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case11_'+GL+'_'+IFX+'ifidx_0glw.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case12_425gldep_675bathydep.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case17_'+GL+'_-66ifidx_0glw.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case18_0glidx_'+IFX+'ifidx_623_0glw.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case7_0glidx_'+IFX+'ifidx_623_0glw.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case20_'+GL+'_-66ifidx_0glw.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case21_0glidx_'+IFX+'ifidx_623_0glw.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case24_0glidx_'+IFX+'ifidx_623_0glw.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case25_0glidx_'+IFX+'ifidx_623_0glw.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case26_0glidx_'+IFX+'ifidx_623_0glw.nc'

            #BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case10_'+IFX+'glw.nc'

            BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case27_0glidx_'+IFX+'ifidx_623_0glw.nc'
            BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case27_0glidx_-36ifidx_623_0glw_w11.nc'
            BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_case27_0glidx_-36ifidx_623_0glw_w'+CASE+'.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/bfile_c28_0glidx_-30ifidx_623_0glw_w'+tsfile+'.nc'
            #BFILE=WCONFIG+'/20200804_slopeVmelt/bfile_c30_0glidx_'+IFX+'ifidx_623_0glw_w'+tsfile+'.nc'
            BFILE=WCONFIG+'/20200804_slopeVmelt/new_bathy_c31_0glidx_-37ifidx_982_0glw_w10.nc'

            #NEMOdir="/work/n02/n02/chbull/nemo/models/MergedCode_9321_flx9855_remap9853_divgcorr9845_shlat9864"
            NEMOdir='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/'

            #NEMO code modifications used for RR-AJ slopeVmelt (paper_case='20200804_slopeVmelt') with updated sbcfwb (see email from Robin on Aug 11, 2020, 10:03 PM). Specifically, sbcfwb.f90 now includes this line:
                #sfx(:,:) = sfx(:,:) + z_fwf * sss_m(:,:) * tmask(:,:,1)
            #NEMOexe='/work/n02/n02/chbull/nemo/models/MergedCode_9321_flx9855_remap9853_divgcorr9845_shlat9864/NEMOGCM/CONFIG/slopeVmelt/BLD/bin/nemo.exe'
            #NEMOexe='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/nemo36/NEMOGCM/CONFIG/slopeVmelt/BLD/bin/nemo.exe'
            NEMOexe='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/tests/slopeVmelt/BLD/bin/nemo.exe'
            #print(bcolors.WARNING + "WARNING: "  +'Hard overwriting'+  bcolors.ENDC + ' of NEMO version!')
          
            #NEMOexe=/work/n02/n02/chbull/nemo/models/MergedCode_G06-9321_isf-remap-9853_shlat2d-9854_isf-flx-986/CONFIG/WED025_3/BLD/bin/nemo.exe
            #echo "WARNING: Hard overwriting of NEMO version to weddell sea configuration"

            TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_slopeVmelt_01deg_348sal.nc'
            TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_slopeVmelt_01deg_348sal_w11.nc'
            TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_slopeVmelt_01deg_348sal_w'+CASE+'.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_c28_01deg_348sal_w'+tsfile+'.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_c29_WARM_w'+tsfile+'.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_c30_WARM_w'+tsfile+'.nc'

            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_nemo_base_WARM-NEWFIX_ngrid.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_nemo_base_COLD-NEWFIX_ngrid.nc'

            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_uHuD_Toff_-1.5.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_uHuD_Toff_-1.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_uHuD_Toff_-0.5.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_uHuD_Toff_0.5.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_uHuD_Toff_1.0.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_uHuD_Toff_1.5.nc'

            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_uHuD_Tgrad_'+tsfile+'.nc'
            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_uHuD_Sgrad_'+tsfile+'.nc'

            #TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_slopeVmelt_01deg_348sal_rm'+tsfile+'.nc'
            TSFILE=WCONFIG+'/20200804_slopeVmelt/TS_init_c31_WARM_slopeVmelt_w10.nc'

            rP_nml_domcfgpatch={}
            rP_nml_domcfgpatch['namcfg']={'jpiglo':10,'jpidta':10}
            rP_nml_domcfgpatch['namcfg']={'jpiglo':int(10),'jpidta':int(10),'jpjglo':int(50),'jpjdta':int(50)}
            rP_nml_domcfgpatch['namdom']={'pphmax':float(2000.0)}
            customdomcfg=['','']
        elif rP_CONFIG_TYPE=="AJTOY":
            #rP_CONFIG='ajtoy_FLAT'
            rP_CONFIG='ajtoy_SLPD'
            rP_CONFIG='ajtoy_ESLPD'
            rP_CONFIG='ajtoy_SSLPD'
            #rP_CONFIG='ajtoy_SLPD_REENT'

            rP_CONFIG='ajtoy_05Fsl_FB'
            rP_CONFIG='ajtoy_10Fsl_FB'
            rP_CONFIG='ajtoy_10Fsl_FB_MOVIE'
            #rP_CONFIG='ajtoy_15Fsl_FB'
            #rP_CONFIG='ajtoy_10Fsl_FB_SSIDE'
            #rP_CONFIG='ajtoy_10Fsl_FB_EWALL'
            #rP_CONFIG='ajtoy_10Fsl_FB_ESLPD'
            #rP_CONFIG='ajtoy_10Fsl_FB_ESLPDL'
            #rP_CONFIG='ajtoy_10Fsl_FB_SSLPD_MOVIE'
            #rP_CONFIG='ajtoy_10Fsl_FB_SSLPDL'
            WCONFIG='/work/n02/n02/chbull/nemo/bld_configs/input_ajtoy'
            NEMOdir="/work/n02/n02/chbull/nemo/models/MergedCode_9321_flx9855_remap9853_divgcorr9845_shlat9864"
            #NEMOexe=${NEMOdir}/NEMOGCM/CONFIG/${rP_CONFIG}/BLD/bin/nemo.exe
            NEMOdir='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/'

            #NEMOexe='/work/n02/n02/chbull/nemo/models/MergedCode_9321_flx9855_remap9853_divgcorr9845_shlat9864/NEMOGCM/CONFIG/aj_ts_melt_off_dynlin2/BLD/bin/nemo.exe'
            #NEMOexe='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/nemo36/NEMOGCM/CONFIG/aj_ts_melt_off/BLD/bin/nemo.exe'
            #NEMOexe='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/tests/aj_ts_melt_off/BLD/bin/nemo.exe'
            #NEMOexe='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/nemo36/NEMOGCM/CONFIG/aj_ts_melt_off_dynlin/BLD/bin/nemo.exe'
            NEMOexe='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/tests/aj_ts_melt_off2/BLD/bin/nemo.exe'
            print(bcolors.WARNING + "WARNING: "  +'Hard overwriting'+  bcolors.ENDC + ' of NEMO version to aj_ts_melt_off2 (ARCHER2)')

            BFILE=WCONFIG+'/new_bathy.nc'
            BFILE=WCONFIG+'/new_sloping_bathy.nc'    #sloping no surface -  "SLPD"
            BFILE=WCONFIG+'/new_bathy_sloping.nc'  #ESLPD
            BFILE=WCONFIG+'/new_bathy_slopingsideonly.nc' #SSLPD
            #BFILE=WCONFIG+'/new_bathy_slopingboth.nc' #was incorrect somehow, now deleted

            BFILE=WCONFIG+'/new_bathy_FB.nc' #Flat bottom
            #BFILE=WCONFIG+'/new_bathy_FB_slpdendwall.nc' #Flat bottom with sloped endwalls
            #BFILE=WCONFIG+'/new_bathy_FB_slpdendwall_long.nc' #Flat bottom with *long* sloped endwalls
            #BFILE=WCONFIG+'/new_bathy_FB_slpdside.nc' #Flat bottom with sloped sidewalls
            #BFILE=WCONFIG+'/new_bathy_FB_slpdside_long.nc' #Flat bottom with *long* sloped sidewalls


            TSFILE=WCONFIG+'/TS_init_rho1_uHoz_uVert.nc'
            TSFILE=WCONFIG+'/TS_init_rho1_uHoz_uVert_05slpd.nc'
            TSFILE=WCONFIG+'/TS_init_rho1_uHoz_uVert_10slpd.nc'
            #TSFILE=WCONFIG+'/TS_init_rho1_uHoz_uVert_15slpd.nc'
            print(bcolors.WARNING + "WARNING: "  +'Hard overwriting'+  bcolors.ENDC + ' of TSFILE with constant T/S, namely: ' + os.path.basename(TSFILE))
            rP_nml_domcfgpatch={}
            #rP_nml_domcfgpatch['namcfg']={'jperio':int(1)}
            flxfce=''
            customdomcfg=['','']
        elif rP_CONFIG_TYPE=="ASF":
            #rP_CONFIG='asf_c'+str(NUM)+'MOthickPROD'
            rP_CONFIG='asf_c'+str(NUM)
            WCONFIG='/work/n02/n02/chbull/nemo/bld_configs/input_ASF'
            NEMOdir='/work/n02/n02/chbull/nemo/models/NEMO404_MO/'
            NEMOexe='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/tests/asfdyn/BLD/bin/nemo.exe'
            NEMOexe='/work/n02/n02/chbull/nemo/models/NEMO404_MO/tests/asfdyn/BLD/bin/nemo.exe'
            #BFILE=WCONFIG+'/new_bathy_ASF_c01.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c01_retrograde.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c02_flat_isfuni.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c03_flat_isfpinch.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c05_500km_ridge.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c06_750km_ridge.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c07_1000km_ridge.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c08_walledisf.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c13_killisf.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c13.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c'+str(BFNUM)+'.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c'+str(BFNUM)+'_killisf.nc'

            #BFILE=WCONFIG+'/new_bathy_ASF_c28_killisf_fullwall.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c29_killisf_shelfwall.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c30_killisf_oowall.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c16_killisf.nc'

            #update: 6/2/24 new bathymetries for re-runs for paper revision
            BFILE=WCONFIG+'/new_bathy_ASF_c40_deeprid_fullwall.nc'
            BFILE=WCONFIG+'/new_bathy_ASF_c38_deeprid_shelfwall.nc'
            BFILE=WCONFIG+'/new_bathy_ASF_c39_deeprid_oowall.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c37_deeprid.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c16_killisf.nc'

            #BFILE=WCONFIG+'/new_bathy_ASF_c28_fullwall.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c29_shelfwall.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c30_oowall.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c36_none.nc'

            #BFILE=WCONFIG+'/new_bathy_ASF_c31_killisf_d500.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c32_killisf_d1000.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c33_killisf_d1500.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c34_killisf_d2000.nc'
            #BFILE=WCONFIG+'/new_bathy_ASF_c35_killisf_d2500.nc'

            TSFILE=WCONFIG+'/TS_init_c01_01deg_348sal_ASF.nc'
            TSFILE=WCONFIG+'/TS_init_c01_WARM_ASF.nc'
            #new world ocean at last restoring and initial conditions
            TSFILE=WCONFIG+'/TS_init_c02_woa2018.nc'
            TSFILE=WCONFIG+'/TS_init_c03_woa2018.nc'
            flxfce='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/bld_configs/input_ASF/flxforce_grid_.nc'
            flxfce='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/bld_configs/input_ASF/flxforce_ujet020isfonly_grid_.nc'
            #flxfce='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/bld_configs/input_ASF/flxforce_case'+NUM+'_grid_.nc'
            #flxfce='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/bld_configs/input_ASF/flxforce_case02_grid_.nc'
            #flxfce='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/bld_configs/input_ASF/flxforce_case03_grid_.nc'
            #flxfce='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/bld_configs/input_ASF/flxforce_case'+'01'+'_grid_.nc'
            #flxfce='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/bld_configs/input_ASF/flxforce_case'+'14'+'_grid_.nc'
            flxfce='/work/n02/n02/chbull/nemo/bld_configs/input_ASF/flxforce_case'+str(flx)+'_grid_.nc'
            
            #rP_nml_domcfgpatch={}
            #rP_nml_domcfgpatch['namcfg']={'jpiglo':int(257),'jpidta':int(257),'jpjglo':int(385),'jpjdta':int(385),'jperio':int(1)}
            #rP_nml_domcfgpatch['namdom']={'pphmax':float(3000.0)}

            #'standard' NEMO 75 levels (I think) based on
            #http://pp.ige-grenoble.fr/pageperso/jourdai1/NEMO-raijin.html
            #https://pmathiot.github.io/NEMOCFG/docs/build/html/input_eORCA025.html
            #/mnt/lustre/a2fs-work2/work/n02/n02/chbull/repos/nemo_wed_analysis/ajtoy/diagnostics/zgr_slider.py
            rP_nml_domcfgpatch={}
            rP_nml_domcfgpatch['namcfg']={'jpiglo':int(257),'jpidta':int(257),'jpjglo':int(385),'jpjdta':int(385),'jpkdta':int(75),'jperio':int(1)} #NB 75 levs
            rP_nml_domcfgpatch['namdom']={'ppkth' : 15.35101370000000,'ppacr' : 7.,'ppdzmin' : 0,'pphmax' : 0,'ppsur' : -3958.951371276829,'ppa0' : 103.9530096000000,'ppa1' : 2.415951269000000,'ldbletanh' : True,'ppa2  ': 100.7609285000000,'ppkth2': 48.02989372000000,'ppacr2': 13.00000000000}

            #customdomcfg=['rogue','/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/bld_configs/input_ASF/domain_cfg_61DM.nc']
            #customdomcfg=['','']
            customdomcfg=['hacked','/mnt/lustre/a2fs-work2/work/n02/n02/chbull/repos/nemo_wed_analysis/ajtoy/diagnostics/mk_domaincfg.py']

            #turn off ice-shelf
            rP_nml_domcfgpatch['namzgr']={'ln_isfcav':False}
            rP_nml_patch={}
            rP_nml_patch['namdyn_hpg']={'ln_hpg_isf':False,'ln_hpg_sco':True}
            rP_nml_patch['namsbc']={'ln_isf':False}

            #update: 6/2/24 new bathymetries for re-runs for paper revision -- turning on GM
            #see email from Dave Nov 3, 2023, 2:54 PM / Re: an idealized southern ocean channel configuration.
            #suggested aei0=2000 was a good starting point
            rP_nml_patch['namtra_eiv']={'ln_ldfeiv':True,'ln_ldfeiv_dia':True}

            #this is true only if you want to use an existing bathymetry, it will hack from a passed file
            #mkillisf=True

            #turn on dyntrd - nb rP_nml_patch edits above
            #rP_nml_patch['namtrd']={'ln_dyn_trd':True}
        elif rP_CONFIG_TYPE=="SR_ML":
            WCONFIG='/mnt/lustre/a2fs-work2/work/n02/shared/chbull/SR_64x64_N100'
            WCONFIG='/work/n02/shared/chbull/SR_64x64_NewBathyTest'
            WCONFIG='/mnt/lustre/a2fs-work2/work/n02/shared/shrr/output_tests_v2'
            NEMOdir='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/'
            NEMOexe='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/tests/slopeVmelt/BLD/bin/nemo.exe'
            #sebastian's wacky geometries
            #BFILE='/mnt/lustre/a2fs-work2/work/n02/shared/chbull/SR_64x64_test/bathy_meter_Exp00003.nc'
            #TSFILE='/mnt/lustre/a2fs-work2/work/n02/shared/chbull/SR_64x64_test/TS_init_Exp00003.nc'
            BFILE =WCONFIG+'/bathy_meter_Exp'+str(NUM).zfill(5)+'.nc'
            TSFILE=WCONFIG+'/TS_init_Exp'+str(NUM).zfill(5)+'.nc'
            rP_nml_domcfgpatch={}
            rP_nml_domcfgpatch['namcfg']={'jpiglo':int(64),'jpidta':int(64),'jpjglo':int(64),'jpjdta':int(64)}
            rP_nml_domcfgpatch['namdom']={'pphmax':float(2000.0)}
            flxfce=''
            customdomcfg=['','']
        else:
            print(bcolors.FAIL + "We are using config_type: "+rP_CONFIG_TYPE + bcolors.ENDC)
            print(bcolors.FAIL + "E R R O R: I don't know what to do with this config type."+ bcolors.ENDC)
            sys.exit()

        print(bcolors.WARNING + "WARNING: "  +'Hard overwriting'+  bcolors.ENDC + ' of NEMO version')

        rP_WORKDIR=main(workfol,rP_CONFIG,rP_CONFIG_TYPE,rP_CASE,NEMOexe,WCONFIG,BFILE,TSFILE,FLXFCE=flxfce,rP_nml_patch=rP_nml_patch,extdomaincfg=customdomcfg)

        domaincfg='/mnt/lustre/a2fs-work2/work/n02/n02/chbull/nemo/models/NEMO4/tools/DOMAINcfg/BLD/bin/make_domain_cfg.exe'
        mkmesh(workfol,rP_WORKDIR,domaincfg,BFILE,rP_nml_patch=rP_nml_domcfgpatch,killisf=mkillisf,extdomaincfg=customdomcfg)
        #subprocess.call('cd '+rP_WORKDIR+' ; sbatch '+rP_WORKDIR+'/goNEMOquick.sh',shell=True)
        #subprocess.call('cd '+rP_WORKDIR+'; sbatch '+rP_WORKDIR+'/goNEMOlong.sh',shell=True)
        subprocess.call('cd '+rP_WORKDIR+'; sbatch '+rP_WORKDIR+'/goNEMOproduction.sh',shell=True)
