import os, sys
import datetime

# analyzeData takes a string of difference values and determines where a train
# is likely to be passing based on a higher and sustained level of change
def analyzeData(values, setting=None):
    #vidEnd is the last frame in the clip
    vidEnd = len(values)

    # See getParams below
    (diffThresh, toggleON, toggleOFF, buf, _) = getParams(setting=setting)

    # First we filter the data so that we have a list of booleans indicating
    # whether each frame is above the different threshold or not. This is 
    # a high-pass filter
    highPass = map(lambda x: x >= diffThresh, values)

    # clips stores tuples containing start (startFrame) and end (endFrame) times 
    # and length in frames for every clip fully encapsulated in the video
    clips = []
    startFrame = 0
    endFrame = 0

    # train indicates whether we believe a train is present. We start with it
    # on to catch any train tails at the beginning of the clip
    train = True

    # clipTail and clipHead are variables used to store train fragments that may
    # occur at either end of the clip. They are returned separately and combined
    # if necessary 
    clipTail = None
    clipHead = None

    # frameCount keeps track of which frame we are on for indexing
    frameCount = 0

    # counter keeps track of how many frames in a row have disagreed with the 
    # current train status. When this value reaches the toggle thresholds, 
    # we toggle the train status
    counter = 0

    for frame in highPass:
        #print("%d - f: %d, b: %d, d: %d" % (frame, frameCount, counter, train))
        if frame == 1:
            # If train is false, but the frame has a high difference 
            # value, either increment the counter or, if the toggleON threshold 
            # has been reached, reset counter and turn on train, storing the 
            # start time in startFrame
            if train == False:
                if counter == toggleON:
                    counter = 0
                    train = True
                    startFrame = frameCount - toggleON
                else:
                    counter += 1
            # If train and frame both indicate no train, reset the counter
            else:
                counter = 0
        elif frame == 0:
            # If train is true but the frame has a low difference value, 
            # either increment the counter or, if the toggleOFF threshold
            # has been reached, reset the counter and turn off train, storing 
            # the end time in endFrame if the full clip is greater than minLength 
            if train == True:
                if counter == toggleOFF:
                    counter = 0
                    train = False
                    endFrame = frameCount - toggleOFF
                    # If this train clip began near the first frame of the clip, 
                    # consider is the tail end of a larger train and store it
                    # in clipTail
                    if startFrame == 0:
                        if endFrame != 0:
                            clipTail = \
                                ("00:00", timestamp(min(endFrame + buf, vidEnd)), \
                                    endFrame)
                    else:
                        clips += [(timestamp(max(startFrame - buf, 0)), \
                                    timestamp(min(endFrame + buf, vidEnd)), \
                                    endFrame - startFrame)]
                else:
                    counter += 1
            # If train is true and frame is high, reset the counter
            else:
                counter = 0
        frameCount += 1

    # If a train clip was still being recorded at the end of the clip, store this 
    # as the head of a new train in clipHead
    if train == True:
        clipHead = (timestamp(startFrame), timestamp(frameCount + 24), \
            frameCount - startFrame)

    # Return the partial trains (clipTail and clipHead) at beginning and end 
    # along with the full trains (clips)
    return (clipTail, clips, clipHead)


# cut takes a video path along with a start and end time and uses ffmpeg to remove
# that chunk of video and save it at the destination outPath/tag
def cut(vidPath, tag, start, end, outPath):
    outFile = outPath + "/T_%s.mov" % (str(tag).replace(' ', '_'))
    os.system("ffmpeg -i %s -ss %s -deinterlace -to %s \
        -metadata comment=\"%s-%s : %s\" %s" % \
        (vidPath, start, end, start, end, vidPath, outFile))

    print("ffmpeg -i %s -ss %s -deinterlace -to %s -metadata comment=\"%s-%s : %s\" %s" % \
        (vidPath, start, end, start, end, vidPath, outFile))
    return outFile


# getTag takes an existing video, a start time in reference to that video, and the 
# number of frames in that video and calculates a suitable (mostly) unique tag for that clip
# based of the string version of the calculated datetimestamp for that clip
def getTag(vidPath, start, vidFrames):
    lastModified = datetime.datetime.fromtimestamp(os.stat(vidPath).st_mtime)
    vidLength = datetime.timedelta(seconds=(vidFrames/24))
    createTime = lastModified - vidLength

    tag = createTime + makeTimedelta(start)

    # Remove microseconds from tag for visual clarity. This means that the file might 
    # not be unique if two clips are taken within microseconds of each other, but that
    # seems silly
    tag = tag - datetime.timedelta(microseconds=tag.microsecond)
    return str(tag)


# combine takes that paths of two video clips and runs ffmpeg to combine them into 
# one single video at the destination outPath/tag
def combine(path1, path2, tag, outPath):   
    os.system("ffmpeg -i %s -i %s -filter_complex 'concat' %s" \
                % (path1, path2, "%s/%s" % (outPath, tag)))
    os.system("rm %s" % path1)
    os.system("rm %s" % path2)


# timeStamp takes a frame and calculates the timestamp that that frame occurs in a video
# NOTE: because we only eve dealt with 17 minute video, this function does not calculate
# hour in the timestamp
def timestamp(frame):
    seconds = frame / 24
    minutes = seconds / 60
    timestamp = "%02d:%02d" % (minutes, (seconds % 60))

    return timestamp


# calcFrame takes a timestamp (just minutes and seconds, see above) and calculates the 
# frame that the timestamp refers to. This function and the timestamp function are NOT
# reversible because several frames might occur within the same timestamp 
# (for example if the video is 24 frames per second, then 24 frames will share a timestamp)
def calcFrame(timestamp):
    values = timestamp.split(":")
    mins = int(values[0])
    secs = int(values[1])

    return ((mins * 60) + secs) * 24


# makeTimeDelta takes a timestamp and creates an instance of the timedelta class for the
# purpose of adding it to a timestamp
def makeTimedelta(timestamp):
    values = timestamp.split(":")
    mins = int(values[0])
    secs = int(values[1])

    return datetime.timedelta(minutes=mins, seconds=secs)


# findBatch returns a sorted list of every .MTS file located at path. Generally, this
# code requires a sequence of .MTS videos starting at 00000.MTS and counting up
def findBatch(path, ext):
    batch = filter(lambda x: ext in x, os.listdir(path))
    return sorted(batch)


# getParams is the control panel for both trainUtil and findTrains.
# Here you can change all of the parameters that optimize the algorithm
def getParams(setting=None):

    if setting == "h":
        return (3.5, 6*24, 4*24, 6*24, 15*24)
    elif setting == "r":
        return (4, 5*24, 4*24, 6*24, 15*24)
    elif setting == "c":
        return (7.5, 5*24, 4*24, 6*24, 15*24)
    elif setting == "s":
        return (4, 5*24, 4*24, 6*24, 15*24)
    elif setting == "p":
        return (3, 5*24, 4*24, 6*24, 15*24)
    # **** ADD NEW PARAMETER OPTIONS HERE ****
    # Just change the character to some unused string and enter your values into
    # the tuple:
    #elif setting == "p":
    #    return (3, 5*24, 4*24, 6*24, 15*24)

    # diffThresh is the value above which we believe a difference
    # in pixel values indicates a train is present in the video clip
    # Lowering this value increases sensitivity
    diffThresh = 2.5

    # toggleON and toggleOFF are the number of frames (at 24 frames per second)
    # that we will wait before toggling the status on to indicate that we believe 
    # a train is present or off to indicate that we believe no train is present 
    toggleON = 5 * 24
    toggleOFF = 4 * 24

    # buf is a buffer of space added at either end of the clip to ensure that 
    # both ends of the train are captured
    buf = 6 * 24

    # minLength is the minimum number of frames that we will consider a viable clip
    minLength = 15 * 24

    return (diffThresh, toggleON, toggleOFF, buf, minLength)
