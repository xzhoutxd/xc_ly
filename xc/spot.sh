#!/bin/sh

DATESTR=`date +"%Y%m%d%H"`

if [ $# = 0 ]; then
    echo " Usage: $0 master|slave" 
    echo " e.g. : $0 m|s" 
    exit 1
else
    m_type=$1
fi
DIR=`pwd`
cd $DIR
/bin/sh $DIR/k.sh XCSpot python python

cd $DIR/../..
LOGDIR=`pwd`
LOGFILE=$LOGDIR/logs/xc_ly/channel/add_channel_${DATESTR}.log

cd $DIR
/usr/local/bin/python $DIR/XCSpot.py $m_type

## process queue
#p_num=3
#obj='item'
#crawl_type='spot'
#DIR=`pwd`
#cd $DIR
#/bin/sh $DIR/k.sh XCWorkerM $obj $crawl_type

#cd $DIR/../..
#LOGDIR=`pwd`
#LOGFILE=$LOGDIR/logs/xc/channel/add_spots_${DATESTR}.log

#cd $DIR
#/usr/local/bin/python $DIR/XCWorkerM.py $p_num $obj $crawl_type

