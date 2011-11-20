#!/bin/bash

. package_defines.sh

svn export src $RELEASE_NAME.orig
cd $RELEASE_NAME.orig
rm -r debian
cd ..
svn export src $RELEASE_NAME
cd $RELEASE_NAME
debuild
cd ..
rm -r $RELEASE_NAME





echo "I can upload a new binary release to Google Code."
echo -n "Do you want me to? [y/N]: "
read character
case $character in
    [Yy] ) echo "You responded in the affirmative."
	wget http://support.googlecode.com/svn/trunk/scripts/googlecode_upload.py
	chmod a+x googlecode_upload.py
	./googlecode_upload.py -s "Ubuntu package" -p $PROJECT_ID *.deb
	rm googlecode_upload.py
        ;;
    * ) echo "Fine, then."
esac





echo -n "Do you want to install the new .deb? [y/N]: "
read character
case $character in
    [Yy] ) echo "You responded in the affirmative."
	sudo gdebi *.deb
        ;;
    * ) echo "Fine, then."
esac
