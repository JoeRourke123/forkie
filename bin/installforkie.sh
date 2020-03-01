#!/bin/bash

# Will take an output argument and then will check if forkie is already installed in that location

TOKEN="bb15550805756f28d4da829116e175c852d59250"
REQUIREMENTS=( "curl" "pip3" )
UNNECESSARY_FILES=( "forkie_runner.py" "MANIFEST.in" "requirements_cli.txt" "setup.py" "forkie.tar.gz" )
UNNECESSARY_DIRS=( "client" "res" )


usage() {
    echo "usage: installforkie.sh [-o <output> | -h]"
}

# Checks given command installed (from: https://stackoverflow.com/questions/7292584/how-to-check-if-git-is-installed-from-bashrc/7292650)
check_if_installed() {
    $1 --version 2>&1 >/dev/null
    IS_AVAILABLE=$?
    if [ ! $IS_AVAILABLE -eq 0 ]; then
        echo "'$1' is not installed. Please install $1 and then try again"
        exit 1
    fi
}

remove_dir-f() {
    rm -rf $1
}

remove_file-f() {
    rm -f $1
}

# Handles args (from: http://linuxcommand.org/lc3_wss0120.php)
output=$PWD
while [ "$1" != "" ]; do
    case $1 in
        -o | --output ) shift
                        output=$1
                        ;;
        -h | --help )   usage
                        exit
                        ;;
        * )             usage
                        exit 1
                        ;;
    esac
    shift
done

# Checks if all requirements are installed
for i in "${REQUIREMENTS[@]}"
do
	check_if_installed $i
done

# If file output argument exists
if [ "$output" != "" ]; then
    # Check if install location exists
    if [ ! -d "$output" ]; then
        echo "Specified install location does not exist. Stopping..."
        exit 1
    fi

    # Check if the output location contains app.py
    if [ -f "$output/app.py" ]; then
        if [ "$PWD" != "$output" -a "$output" != "." ]; then
            response=
            echo -n "Forkie is already installed in that location. Do you want to install in '$PWD'? (y/n) > "
            read response
            if [ "$response" != "y" ]; then
                echo "Exiting..."
                exit 1
            else
                output="$PWD"
            fi
        else
            echo "Forkie is already installed in the cwd. Exiting..."
            exit 1
        fi
    else
        output=$output
    fi
fi
echo "Installing forkie in '$output'"

# Uses the github api along with the oauth token to get the latest commit of master
printf "\nGetting latest forkie build from github\n"
curl -H "Authorization: token $TOKEN" -L https://api.github.com/repos/RHUL-CS-Projects/CS1813_2020_09/tarball/master > "$output/forkie.tar.gz"

echo "Extracting tar"
tar -xf "$output/forkie.tar.gz" -C $output

echo "Moving extracted contents into output directory"
mv $(find $output -name RHUL-CS-Projects-CS1813_2020_09* -type d | sed 1q)/* $output
mv $(find $output -name RHUL-CS-Projects-CS1813_2020_09* -type d | sed 1q)/.slugignore $output

echo "Deleting unnecessary files and packages"
rm -rf $(find $output -name RHUL-CS-Projects-CS1813_2020_09* -type d | sed 1q)
for i in "${UNNECESSARY_FILES[@]}"
do
	remove_file-f "$output/$i"
done
for i in "${UNNECESSARY_DIRS[@]}"
do
	remove_dir-f "$output/$i"
done

response=
echo -n "Do you want to pip install requirements.txt? (y/n) > "
read response
if [ $response == "y" ]; then
    pip3 install -r "$output/requirements.txt"
fi
printf "\nFinished forkie setup\nTo start the forkie web server on localhost run the 'forkielocal.sh' script\n"

exit 1