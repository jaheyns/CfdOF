cd $WM_PROJECT_USER_DIR &&
{
cd cfMesh-v1.1.2 &&
{

echo "Cleaning..."
./Allwclean

echo "Getting include file name translations..."
cd $WM_PROJECT_DIR
Tfiles=$(find -name "*.T.H" | sed -r 's#.*/(.*).T.H#\1#')
Tfiles="($(echo $Tfiles | sed 'y/ /|/'))"
sedscr='s/\#include "'$Tfiles'\.H"/#include "\1.T.H"/'
cd -

echo "Changing include file names..."
for f in `find -name "*.H"` `find -name "*.C"`
do
    sed -i -r "$sedscr" "$f"
done

echo "Modifying library includes..."
sed -i -r 's/^[[:space:]]*LIBS =[[:space:]]*$/\0 -lmeshTools -ledgeMesh -ltriSurface/' meshLibrary/Make/options

echo "Building..."
./Allwmake

echo "Running second build to fix up..."
./Allwmake
}
}
