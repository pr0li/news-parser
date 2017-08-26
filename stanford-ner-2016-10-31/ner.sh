#!/bin/sh
scriptdir=`dirname $0`

java -mx2g -cp "$scriptdir/stanford-ner.jar:$scriptdir/lib/*" edu.stanford.nlp.ie.crf.CRFClassifier -loadClassifier $scriptdir/classifiers/spanish.ancora.distsim.s512.crf.ser.gz -textFile $1
