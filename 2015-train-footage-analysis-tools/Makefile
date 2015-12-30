# This Makefile runs the difference filter between every frame of a video to calculate the change

# It is hardcoded to run on .MTS video and with a specific file structure:
#	ffmpeg is installed (located /usr/local/bin/ffmpeg)
#	difference-filter is located ~/tmThumbnail/filters/difference-filter

# The result is a folder called data containing a json file for every video file.
# The json file is an array of difference calculations between frames, so the length
# of the array would be n-1

all: $(patsubst %.MTS,%.json,$(wildcard *.MTS))

%.json: %.MTS
	mkdir -p data
	/usr/local/bin/ffmpeg -threads 8 -y -i $^ -vf scale=240:-1 -f rawvideo -pix_fmt \
		rgb24 pipe:1 | ~/tmThumbnail/filters/difference-filter --width 240 --height 135 \
		> $@.tmp.json
	mv $@.tmp.json data/$@

clean:
	rm *.json
	rm data/*.json
	rmdir data