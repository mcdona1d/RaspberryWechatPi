#!/bin/sh

STREAMER=mjpg_streamer
DEVICE=/dev/video0
RESOLUTION=320x240
FRAMERATE=10
HTTP_PORT=8001

PLUGINPATH=/usr/lib

#$STREAMER -i "$PLUGINPATH/input_uvc.so -n -d $DEVICE -r $RESOLUTION -f $FRAMERATE" -o "$PLUGINPATH/output_http.so -n -p $HTTP_PORT " &
$STREAMER -i "$PLUGINPATH/input_uvc.so -n -d $DEVICE -r $RESOLUTION -f $FRAMERATE -y YUYV" -o "$PLUGINPATH/output_http.so -n -p $HTTP_PORT " &

