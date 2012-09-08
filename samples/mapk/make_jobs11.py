#!/usr/bin/python


template = '''
#!/bin/sh

## $ -V
#$ -v PYTHONPATH=$PYTHONPATH:/home/shafi/wrk/epdp
#$ -v LOGLEVEL=ERROR
#$ -v LOGFILE=/tmp/%s.log
#$ -v LOGSIZE=10000
#$ -cwd

LOGFILE=/tmp/%s.log

success()
{
    echo 'ok'
    /bin/mv $JOB_NAME done.$JOB_NAME
    cleanup
}

fail()
{
    echo 'fail'
    /bin/mv $JOB_NAME fail.$JOB_NAME
    cleanup
    exit 1
}

interrupted()
{
    echo "interrupted..."
    trap '' 2 9 15
    fail
    exit 1
}

cleanup()
{
    /bin/mv $LOGFILE .
}

trap interrupted 2 9 15

python -O /home/shafi/wrk/models/mapk/model4.py %s

if [ $? = 0 ]
then
    success
else
    fail
fi


'''

prefix = 'run_'
model = 'mapk4'

def createJobFile( V, D_ratio, D_mode, N_K_total, Kpp_ratio, ti, mode, T ):
    filename = prefix + model + '_' + '_'.join( ( V, D_ratio, D_mode, N_K_total, Kpp_ratio, ti, mode ) ) + '.sh'
    print filename
    #return
    f = open( filename, 'w' )
    args = ' '.join( ( V, D_ratio, D_mode, N_K_total, Kpp_ratio, ti, mode, T ) )
    f.write( template % ( filename, filename, args ) )
    f.close()

def createJobs( V_list, D_ratio_list, D_mode_list, N_K_total_list, Kpp_ratio_list, ti_list, mode_list, T ):

    for V in V_list:
        for D_ratio in D_ratio_list:
            for D_mode in D_mode_list:
                for N_K_total in N_K_total_list:
                    for Kpp_ratio in Kpp_ratio_list:
                        for ti in ti_list:
                            for mode in mode_list:
                                createJobFile( V, D_ratio, D_mode, N_K_total, Kpp_ratio, ti, mode, T )


V_list = [ '1e-15' ]
#D_ratio_list = [ '0.25', '0.5', '1', '2', '4' ]
D_ratio_list = [ '1' ]
#D_mode_list = [ 'normal', 'fixed' ]
D_mode_list = [ 'fixed' ]
#N_K_total_list = ['120', '300']
N_K_total_list = ['300']
Kpp_ratio_list = ['0','.3','.7','1']
ti_list = ['0', '1e-6', '1e-5', '1e-4', '1e-3', '1e-2', '1e-1']
mode_list = ['normal']
T = '400'

createJobs( V_list, D_ratio_list, D_mode_list, N_K_total_list, Kpp_ratio_list, ti_list, mode_list, T )







