import os, sys
import datetime

def analyzeData(values, setting=None):
    #vidEnd is the last frame in the clip
    vidEnd = len(values)

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

    # toggle indicates whether we believe a train is present. We start with it
    # on to catch any train tails at the beginning of the clip
    toggle = 1

    # clipTail and clipHead are variables used to store train fragments that may
    # occur at either end of the clip. They are returned separately and combined 
    clipTail = None
    clipHead = None

    # frameCount keeps track of which frame we are on for indexing
    frameCount = 0

    # counter keeps track of how many frames in a row have disagreed with the 
    # current status. When this value reaches the toggle thresholds, 
    # we toggle the status
    counter = 0

    for frame in highPass:
        #print("%d - f: %d, b: %d, d: %d" % (frame, frameCount, counter, toggle))
        if frame == 1:
            # If toggle indicates no train, but the frame has a high difference 
            # value, either increment the counter or, if the toggleON threshold 
            # has been reached, reset counter and turn on toggle, storing the 
            # start time in startFrame
            if toggle == 0:
                if counter == toggleON:
                    counter = 0
                    toggle = 1
                    startFrame = frameCount - toggleON
                else:
                    counter += 1
            # If toggle and frame both indicate no train, reset the counter
            else:
                counter = 0
        elif frame == 0:
            # If toggle indicates a train but the frame has a low difference 
            # value, either increment the counter or, if the toggleOFF threshold
            # has been reached, reset the counter and turn off toggle, storing 
            # the end time in endFrame if the full clip is greater than minLength 
            if toggle == 1:
                if counter == toggleOFF:
                    counter = 0
                    toggle = 0
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
            # If toggle and frame both indicate a train, reset the counter
            else:
                counter = 0
        frameCount += 1

    # If a train clip was still being recorded at the end of the clip, store this 
    # as the head of a new train in clipHead
    if toggle == 1:
        clipHead = (timestamp(startFrame), timestamp(frameCount + 24), \
            frameCount - startFrame)

    return (clipTail, clips, clipHead, (sum(values)/len(values)))


def cut(vidPath, tag, start, end, outPath):
    outFile = outPath + "/T_%s.mov" % (str(tag).replace(' ', '_'))
    os.system("ffmpeg -i %s -ss %s -deinterlace -to %s \
        -metadata comment=\"%s-%s : %s\" %s" % \
        (vidPath, start, end, start, end, vidPath, outFile))

    print("ffmpeg -i %s -ss %s -deinterlace -to %s -metadata comment=\"%s-%s : %s\" %s" % \
        (vidPath, start, end, start, end, vidPath, outFile))
    return outFile


def getTag(vidPath, start, vidFrames):
    lastModified = datetime.datetime.fromtimestamp(os.stat(vidPath).st_mtime)
    vidLength = datetime.timedelta(seconds=(vidFrames/24))
    createTime = lastModified - vidLength

    tag = createTime + makeTimedelta(start)

    # Remove microseconds from tag for visual clarity
    tag = tag - datetime.timedelta(microseconds=tag.microsecond)
    return str(tag)


def combine(path1, path2, tag, outPath):   
    os.system("ffmpeg -i %s -i %s -filter_complex 'concat' %s" \
                % (path1, path2, "%s/%s" % (outPath, tag)))
    os.system("rm %s" % path1)
    os.system("rm %s" % path2)


def timestamp(frame):
    seconds = frame / 24
    minutes = seconds / 60
    timestamp = "%02d:%02d" % (minutes, (seconds % 60))

    return timestamp

def calcFrame(timestamp):
    values = timestamp.split(":")
    mins = int(values[0])
    secs = int(values[1])

    return ((mins * 60) + secs) * 24


def makeTimedelta(timestamp):
    values = timestamp.split(":")
    mins = int(values[0])
    secs = int(values[1])

    return datetime.timedelta(minutes=mins, seconds=secs)


def findBatch(path):
    batch = filter(lambda x: x[-4:] == ".MTS", os.listdir(path))
    return sorted(batch)


# getParams is the control panel for both trainUtil and findTrains.
# Here you can change all of the aprameters that optimize the algorithm
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

    # diffThresh is the value above which we believe a difference
    # in pixel values indicates a train is present in the video clip
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
