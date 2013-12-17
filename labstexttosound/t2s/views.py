# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from glob import glob
from django.http import HttpResponse
from t2s.models import Tweet
from labstexttosound import settings
# from libs import ApiResponse
import os, subprocess
import uuid
from django.views.decorators.csrf import csrf_exempt
import simplejson
import urllib2
import re
from xml.etree import ElementTree
from t2s.forms import TestForm, PlayLabsmbForm

'''
References:
http://www.zytrax.com/tech/audio/audio.html
https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax
http://stackoverflow.com/questions/11944795/django-middleware-throws-403-error-with-https-post-using-ajax
'''

# TODO: Finish mapping: punctuation?

# Constants.
MOOD_POSITIVE = 'positive'
MOOD_NEGATIVE = 'negative'
SOUND_TYPES = ['sine', 'square', 'triangle', 'sawtooth', 'trapezium', 'exp', 'noise', 'tpdfnoise', 'pinknoise', 'brownnoise', 'pluck']
# SOUND_TYPE = SOUND_TYPES[1]
VOWELS = 'aeiou'
DEFAULT_DURATION = .07
VOWEL_DURATION = .1
SPACE_DURATION = .05
PAD_START = .25
PAD_END = 1
# DEFAULT_DURATION = .1
# VOWEL_DURATION = .18 
# SPACE_DURATION = .8
PITCH_BEND_AMOUNT = .02
INPUT_LENGTH_ZERO_POINT = 15
OCTAVES_UP = 5  # Multiplier, 0 = default pitch.
# REVERB_PARAMS = 'reverb 100 0 100 100 0 10'
REVERB_PARAMS = 'reverb'  # Default parameters.
# REVERB_PARAMS = ''
INPUT_TEXT_MAX_LENGTH = 75
NOTE_MAP = {
           'a': '3-1',
           'b': '3-2',
           'c': '3-3',
           'd': '3-4',
           'e': '3-5',
           'f': '3-6',
           'g': '3-7',
           'h': '4-1',
           'i': '4-2',
           'j': '4-3',
           'k': '4-4',
           'l': '4-5',
           'm': '4-6',
           'n': '4-7',
           'o': '5-1',
           'p': '5-2',
           'q': '5-3',
           'r': '5-4',
           's': '5-5',
           't': '5-6',
           'u': '5-7',
           'v': '6-1',
           'w': '6-2',
           'x': '6-3',
           'y': '6-4',
           'z': '6-5',
           '0': '6-6',
           '1': '6-7',
           '2': '7-1',
           '3': '7-2',
           '4': '7-3',
           '5': '7-4',
           '6': '7-5',
           '7': '7-6',
           '8': '7-7',
           '9': '8-1'
           # etc
           }
FREQUENCY_MAP = {
                '3-1': 131,
                '3-2': 147,
                '3-3-flat': 156,
                '3-3': 165,
                '3-4': 175,
                '3-5': 196,
                '3-6-flat': 208,
                '3-6': 220,
                '3-7': 247,
                '4-1': 262,
                '4-2': 294,
                '4-3-flat': 311,
                '4-3': 330,
                '4-4': 349,
                '4-5': 392,
                '4-6-flat': 415,
                '4-6': 440,
                '4-7': 493,
                '5-1': 523,
                '5-2': 587,
                '5-3-flat': 622,
                '5-3': 659,
                '5-4': 698,
                '5-5': 784,
                '5-6-flat': 831,
                '5-6': 880,
                '5-7': 988,
                '6-1': 1047,
                '6-2': 1175,
                '6-3-flat': 1245,
                '6-3': 1319,
                '6-4': 1397,
                '6-5': 1568,
                '6-6-flat': 1661,
                '6-6': 1760,
                '6-7': 1976,
                '7-1': 2093,
                '7-2': 2349,
                '7-3-flat': 2489,
                '7-3': 2637,
                '7-4': 2794,
                '7-5': 3136,
                '7-6-flat': 3322,
                '7-6': 3520,
                '7-7': 3951,
                '8-1': 4186
                # etc
                }


def playlabsmb(request):
    if request.method == 'POST':
        form = PlayLabsmbForm(request.POST)
        if form.is_valid():
            # Get mood from form post.
            mood = request.POST['mood']
            inputText = []
            # Get text from the LABSmb Twitter, Tumblr, Pinterest and projects feeds...
            twitterApiUrl = 'https://search.twitter.com/search.json?q=%23labsmb&page=1&result_type=recent&rpp=1'
            twitterFeed = __get_json_feed(twitterApiUrl)
            if len(twitterFeed['results']) > 0:
                inputText.append(__sanitize_text(twitterFeed['results'][0]['text'][:INPUT_TEXT_MAX_LENGTH]))
            tumblrTextApiUrl = 'http://labsmb.tumblr.com/api/read/?type=regular&num=1'
            tumblrFeedTree = __get_xml_feed(tumblrTextApiUrl)
            tumblrPosts = tumblrFeedTree.findall('./posts/post/regular-title')
            if (len(tumblrPosts) > 0):
                inputText.append(__sanitize_text(tumblrPosts[0].text[:INPUT_TEXT_MAX_LENGTH]))
            pinterestApiUrl = 'http://pinterest.com/labsmb/labs-inspiration.rss'
            pinterestFeedTree = __get_xml_feed(pinterestApiUrl)
            pinterestPosts = pinterestFeedTree.findall('./channel/item/description')
            if (len(pinterestPosts) > 0):
                inputText.append(__sanitize_text(pinterestPosts[0].text[:INPUT_TEXT_MAX_LENGTH]))
            labsProjectsApiUrl = 'http://www.labsmb.com/search/do_search/'
            labsProjectsFeed = __get_json_feed(labsProjectsApiUrl)
            if len(labsProjectsFeed['do_search']['projects']) > 0:
                inputText.append(__sanitize_text(labsProjectsFeed['do_search']['projects'][0]['intro'][:INPUT_TEXT_MAX_LENGTH]))
            # TODO: Add caching!
            soundUrl = __get_sound_from_text(inputText, mood)
            return HttpResponse('<a href="' + soundUrl + '">' + soundUrl + '</a>')
    else:
        form = PlayLabsmbForm()  # An empty, unbound form
        return render_to_response(
                                  't2s/playlabsmb.html',
                                  {'form': form},
                                  context_instance=RequestContext(request))


def testpost(request):
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            # Split input at comma, into parallel sounds.
            text = request.POST['text'].splitlines()
            mood = request.POST['mood']
            soundUrl = __get_sound_from_text(text, mood)
            return HttpResponse('<a href="' + soundUrl + '">' + soundUrl + '</a>')
    else:
        form = TestForm()  # An empty, unbound form
        return render_to_response(
                                  't2s/testpost.html',
                                  {'form': form},
                                  context_instance=RequestContext(request))


def playtwitterfeed(request):
    tweet = Tweet.objects.order_by('?')[0]
    soundUrl = __get_sound_from_text(tweet.parsed_text.splitlines(), tweet.mood)
    return HttpResponse(soundUrl)


@csrf_exempt
def texttosound(request):
    if request.method == 'POST':
        # Split input at comma, into parallel sounds.
        text = request.POST['text'].strip().splitlines()
        mood = request.POST['mood']
        soundUrl = __get_sound_from_text(text, mood)
        return HttpResponse(soundUrl)
    else:
        # Serve flash file.
        return render_to_response(
                                  't2s/texttosound.html',
                                  {'swf_url': settings.MEDIA_URL},
                                  context_instance=RequestContext(request))


def __get_json_feed(url):
    reqest = urllib2.Request(url)
    opener = urllib2.build_opener()
    f = opener.open(reqest)
    return simplejson.load(f)


def __get_xml_feed(url):
    reqest = urllib2.Request(url)
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    f = opener.open(reqest)
    text = f.read()
    tree = ElementTree.fromstring(text)
    return tree


def __sanitize_text(text):
    return re.sub('[!@#$]', '', text)


def __get_note_params(char, mood, pitchBend=0, durationDivisor=1, octaveMultiplier=0):
    freq = 0
    duration = DEFAULT_DURATION
    if char not in NOTE_MAP.keys():
        return [freq, SPACE_DURATION]
    freqKey = NOTE_MAP[char]
    if mood == MOOD_NEGATIVE and ('-3' in freqKey or '-6' in freqKey):
        freqKey += '-flat'
    # If octaveMultiplier is non-negative, then multiply. If it's negative, divide. Avoid zero multipliers/dividers.
    if octaveMultiplier >= 0:
        freq = FREQUENCY_MAP[freqKey] * (octaveMultiplier + 1)
    elif octaveMultiplier == -1:
        freq = FREQUENCY_MAP[freqKey]
    else:
        freq = FREQUENCY_MAP[freqKey] / abs((octaveMultiplier + 1))
    if freq is None:
        # Sanity check:
        raise Exception('No frequency found. We have a problem!')
    # If the character is a vowel, extent the duration.
    if char in VOWELS:
        duration = VOWEL_DURATION
    # Apply pitch bend (down for negative, up for positive) for certain positions.
    if pitchBend > 0:
        bendFreq = freq * (1 - pitchBend)
        if mood == MOOD_POSITIVE:
            freq = str(bendFreq) + '-' + str(freq)
        else:
            freq = str(freq) + '-' + str(bendFreq)
    # Apply duration divisor.
    duration = duration / durationDivisor
    return [freq, duration] 


def __get_sound_from_text(textArray, mood):
    try:
        if len(textArray) < 1:
            raise Exception('Must supply an input string!')
        # Create unique path.
        uniqueId = str(uuid.uuid4())
        rootPath = os.path.join(settings.MEDIA_ROOT + settings.SOUND_FILES_DIR, uniqueId)
        rootUrl = settings.MEDIA_URL + settings.SOUND_FILES_DIR + '/' + uniqueId + '/'
        os.makedirs(rootPath)
        # Set directory permissions.
        os.chmod(rootPath, 0o777);  # FIXME: Lock this down!
        # For each element in the text array, convert to sound and then mix at the end.
        parallelSounds = []
        for i in range(len(textArray)):
            text = textArray[i].strip().lower()
            mood = mood.strip().lower()
            if len(text) < 1:
                raise Exception('Text input cannot be blank!')
            soundParts = []
            # Calculate duration multiplier based on total input length.
            durationDivisor = round(float(len(text)) / float(INPUT_LENGTH_ZERO_POINT), 2)
            # TODO: Divisor doesn't sound good!
            durationDivisor = 1
            # Pick sound wave type for this text stream.
            if i >= 5:
                soundTypeIndex = 1
            else:
                soundTypeIndex = i
            soundType = SOUND_TYPES[soundTypeIndex]
            octaveMultiplier = OCTAVES_UP - (2 * i)
            # Generate a separate sound file for each character.
            for j in range(len(text)):
                soundPath = os.path.join(rootPath, str(i) + '_' + str(j) + '.wav')
                c = text[j]
                # Do we want a pitch bend?
                if (j == len(text) - 1) or text[j + 1] not in NOTE_MAP.keys():
                    pitchBend = PITCH_BEND_AMOUNT
                else:
                    pitchBend = 0
                [freq, duration] = __get_note_params(c, mood, pitchBend, durationDivisor, octaveMultiplier)
                __generate_sound(soundPath, freq, duration, soundType)
                soundParts.append(soundPath)
            # Now concatenate all the sound files.
            outputFileName = str(i) + '_concat.wav'
            outputFilePath = os.path.join(rootPath, outputFileName)
            __concat_sounds(soundParts, outputFilePath)
            parallelSounds.append(outputFilePath)
        # Now mix all the sound parts.
        mixedFileName = 'sound.mp3'
        mixedFilePath = os.path.join(rootPath, mixedFileName)
        outputFileUrl = rootUrl + mixedFileName
        __mix_sounds(parallelSounds, mixedFilePath)
        # Cleanup.
        for f in glob(os.path.join(rootPath, '*.wav')):
            os.unlink(f)
        return outputFileUrl
    except Exception as ex:
        raise ex


def __mix_sounds(sounds, outputPath):
    # If there is only one element in the list, don't use mix flag.
    if (len(sounds) > 1):
        # Example: sox -m sound1.wav sound2.wav ... soundN.wav finalsound.mp3 [filters...]
        soxCmd = settings.SOX_PATH + ' -m ' + ' '.join(sounds) + ' ' + outputPath + ' ' + REVERB_PARAMS
    elif (len(sounds) == 1):
        # Example: sox sound1.wav sound2.wav ... soundN.wav finalsound.mp3 [filters...]
        soxCmd = settings.SOX_PATH + ' ' + ' '.join(sounds) + ' ' + outputPath + ' ' + REVERB_PARAMS
    else:
        raise Exception('Cannot process blank input!')
    ret = subprocess.call(soxCmd, shell=True)
    if ret > 0:
        raise Exception('SoX mix command failed. Command: ' + soxCmd + ' -- Return code: ' + str(ret))


def __generate_sound(soundPath, freq, duration, soundType):
    # Example: sox -n 1.wav synth .2 sine 1000
    soxCmd = ' '.join([settings.SOX_PATH, '-n', soundPath, 'synth', str(duration), soundType, str(freq)])
    ret = subprocess.call(soxCmd, shell=True)
    if ret > 0:
        raise Exception('SoX synth command failed. Command: ' + soxCmd + ' -- Return code: ' + str(ret))


def __concat_sounds(soundParts, outputFilePath):
    # Example: sox 0.wav 2.wav 3.wav out.mp3 [filters...]
    soxCmd = ' '.join([settings.SOX_PATH, ' '.join(soundParts), outputFilePath, 'pad ' + str(PAD_START) + ' ' + str(PAD_END) + ' gain -30'])
    ret = subprocess.call(soxCmd, shell=True)
    if ret > 0:
        raise Exception('SoX concat command failed. Command: ' + soxCmd + ' -- Return code: ' + str(ret))
