#!/bin/bash
set -e
v=$1
python3 videos.py $v audio
python3 videos.py $v video 0 22.5 ${v}_a_tmp.mp4 & P1=$!
python3 videos.py $v video 22.5 45 ${v}_b_tmp.mp4 & P2=$!
wait $P1; wait $P2
mv ${v}_a_tmp.mp4 ${v}_a.mp4; mv ${v}_b_tmp.mp4 ${v}_b.mp4
printf "file ${v}_a.mp4\nfile ${v}_b.mp4\n" > ${v}_list.txt
ffmpeg -v error -y -f concat -i ${v}_list.txt -c copy ${v}_v.mp4
ffmpeg -v error -y -i ${v}_v.mp4 -i ${v}.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest ${v}_out_tmp.mp4
mv ${v}_out_tmp.mp4 out_${v}.mp4
echo done $v
