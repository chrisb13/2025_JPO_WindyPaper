#basedir='/home/chris/VBoxSHARED4/nemo_output/'
#nemo_fols['asf_c88_00008']=[basedir+'asf_c88_00008/',r"$\delta_{NONE}   \tau_{ -0.1  }$",-0.1 ]
#nemo_fols['asf_c89_00008']=[basedir+'asf_c89_00008/',r"$\delta_{NONE}   \tau_{ -0.05 }$",-0.05]
#nemo_fols['asf_c90_00008']=[basedir+'asf_c90_00008/',r"$\delta_{NONE}   \tau_{ 0     }$",0    ]
#nemo_fols['asf_c91_00008']=[basedir+'asf_c91_00008/',r"$\delta_{NONE}   \tau_{ 0.05  }$",0.05 ]
#nemo_fols['asf_c92_00008']=[basedir+'asf_c92_00008/',r"$\delta_{NONE}   \tau_{ 0.1   }$",0.1  ]

#nemo_fols['asf_c78_00008']=[basedir+'asf_c78_00008/',r"$\delta_{swall} \tau_{ -0.1  }$",-0.1 ]
#nemo_fols['asf_c79_00008']=[basedir+'asf_c79_00008/',r"$\delta_{swall} \tau_{ -0.05 }$",-0.05]
#nemo_fols['asf_c80_00008']=[basedir+'asf_c80_00008/',r"$\delta_{swall} \tau_{ 0     }$",0    ]
#nemo_fols['asf_c81_00008']=[basedir+'asf_c81_00008/',r"$\delta_{swall} \tau_{ 0.05  }$",0.05 ]
#nemo_fols['asf_c82_00008']=[basedir+'asf_c82_00008/',r"$\delta_{swall} \tau_{ 0.1   }$",0.1  ]

#nemo_fols['asf_c83_00008']=[basedir+'asf_c83_00008/',r"$\delta_{oowall}  \tau_{ -0.1  }$",-0.1 ]
#nemo_fols['asf_c84_00008']=[basedir+'asf_c84_00008/',r"$\delta_{oowall}  \tau_{ -0.05 }$",-0.05]
#nemo_fols['asf_c85_00008']=[basedir+'asf_c85_00008/',r"$\delta_{oowall}  \tau_{ 0     }$",0    ]
#nemo_fols['asf_c86_00008']=[basedir+'asf_c86_00008/',r"$\delta_{oowall}  \tau_{ 0.05  }$",0.05 ]
#nemo_fols['asf_c87_00008']=[basedir+'asf_c87_00008/',r"$\delta_{oowall}  \tau_{ 0.1   }$",0.1  ]

#nemo_fols['asf_c73_00008']=[basedir+'asf_c73_00008/',r"$\delta_{wall}    \tau_{ -0.1  }$",-0.1 ]
#nemo_fols['asf_c74_00008']=[basedir+'asf_c74_00008/',r"$\delta_{wall}    \tau_{ -0.05 }$",-0.05]
#nemo_fols['asf_c75_00008']=[basedir+'asf_c75_00008/',r"$\delta_{wall}    \tau_{ 0     }$",0    ]
#nemo_fols['asf_c76_00008']=[basedir+'asf_c76_00008/',r"$\delta_{wall}    \tau_{ 0.05  }$",0.05 ]
#nemo_fols['asf_c77_00008']=[basedir+'asf_c77_00008/',r"$\delta_{wall}    \tau_{ 0.1   }$",0.1  ]

#!/bin/bash
basedir=/home/chris/VBoxSHARED4/nemo_output/
target=/media/DS1/VBoxSHARED4/meh/2025_JPO_WindyPaper/
array=( asf_c88_00008 asf_c89_00008 asf_c90_00008 asf_c91_00008 asf_c92_00008 asf_c78_00008 asf_c79_00008 asf_c80_00008 asf_c81_00008 asf_c82_00008 asf_c83_00008 asf_c84_00008 asf_c85_00008 asf_c86_00008 asf_c87_00008 asf_c73_00008 asf_c74_00008 asf_c75_00008 asf_c76_00008 asf_c77_00008 )
echo 'basedir is'
echo ${basedir}
echo ''
echo 'target is'
echo ${target}
for i in "${array[@]}"
do
    echo $i
    cd ${basedir}${i}
    ls
    mkdir -p ${target}${i}
    cp 0095/namelist*  ${target}${i}
    cp 0095/ocean.output*  ${target}${i}
    cp README ${target}${i}
    cp setupNEMO_ARC2.py ${target}${i}
    cp rPARAMS.py ${target}${i}
    cp domaincfg_namelist* ${target}${i}
done

