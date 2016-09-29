import subprocess

_DEFAULT_FOAM_VERSION = (4,0,0)

#pyhton 2 and 3 has different behavior for subprocess module 

def _detectFoamVersion():
    #foam_ver = subprocess.check_output('bash -i -c "echo $WM_PROJECT_VERSION"')
    proc = subprocess.Popen('bash -i -c "echo $WM_PROJECT_VERSION"', stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (foam_ver, err) = proc.communicate()
    print(err)
    if foam_ver and foam_ver.strip():
        print(foam_ver)
        return tuple([int(s) for s in str(foam_ver).split('.')])
    else:
        print("""environment var 'WM_PROJECT_VERSION' is not defined\n,
              fallback to default {}""".format(_DEFAULT_FOAM_VERSION))
        return _DEFAULT_FOAM_VERSION


#print(_detectFoamVersion())


#using try to finally set a fallback
# all command can not be split, dobuled quote is possible inside single quote
# canot not use ~/.bashrc  even os.path.expenduser()
# windows bash just can not pipe output, how about write into f


#python 3 compatible:     on python 3 output  like this: `b'4.0\n'` or '\n' if not found
#tmp_output = 'tmp_output.txt'  # but current folder may not be writtable
#subprocess.check_output(['bash', '-c', 'source "/opt/openfoam4/etc/bashrc" && echo $WM_PROJECT_VERSION > {}'.format(tmp_output)])
#with open(tmp_output) as f:
#    foam_ver = f.read()
#os.remove() # delete after usage
#source "/opt/openfoam4/etc/bashrc" &&

out = subprocess.check_output(['bash', '-i', '-c', 'simpleFoam -help'], stderr=subprocess.PIPE)
print(out)

foam_dir = subprocess.check_output(['bash', '-i', '-c', 'echo $WM_PROJECT_DIR'], stderr=subprocess.PIPE)
print(len(foam_dir), foam_dir)

foam_ver = subprocess.check_output(['bash', '-i', '-c', 'echo $WM_PROJECT_VERSION'])
#it seems there is warning for `-i` interative mode, but output is fine, stderr=subprocess.PIPE, will suppress the warning msg
print(type(foam_ver))
print(str(foam_ver))
foam_ver = str(foam_ver)
if len(foam_ver)>1:
    if foam_ver[:2] == "b'":
        foam_ver = foam_ver[2:-3] #strip 2 chars from front and tail `b'/opt/openfoam4\n'`
print(tuple([int(s) for s in foam_ver.split('.')]))