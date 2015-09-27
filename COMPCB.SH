#!/bin/sh

if [ -f $1 ]
then
	if [ $(echo $1 | grep .CB$) = "$1" ]
	then
		CBFILE=$(basename "$1")
		OUTEXE="${CBFILE%%.*}"
		OUTFILE="$OUTEXE.C"
		touch $OUTFILE
		if [ ! -f $OUTFILE ]
		then
			echo "Error creating output file, quitting"
			exit
		fi
		echo "#include <stdio.h>" > $OUTFILE
		./CB2C.PY $CBFILE > tempout
		if [ "$?" != "0" ]
		then
			echo "Compilation error: "
			cat tempout
			rm tempout
			exit
		fi
		cat tempout >> $OUTFILE
		gcc -x c $OUTFILE -o $OUTEXE
		rm tempout
	else
		echo "File not Cute BASIC file!"
	fi
fi
