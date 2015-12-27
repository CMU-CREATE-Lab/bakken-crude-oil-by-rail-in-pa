all: $(patsubst %.MTS,%.json,$(wildcard *.MTS))


%.json: %.MTS
	mkdir -p data
	/usr/local/bin/ffmpeg -threads 8 -y -i $^ -vf scale=240:-1 -f rawvideo -pix_fmt rgb24 pipe:1 | ~/tmThumbnail/filters/difference-filter --width 240 --height 135 > $@.tmp.json
	mv $@.tmp.json data/$@

clean:
	rm *.json