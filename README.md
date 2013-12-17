labs-text-to-sound
==================
For this experiment, I built a Django web service that converts character data into sound. Characters were mapped to notes in a C scale. I used octaves 3 through 7 since these center around the most audible frequencies for the human ear. The positive/negative parameter colors the sound (major/minor, respectively).

The goal of this experiment was to design a simple algorithm that lets you "listen" to data. I applied this algorithm to user input text as well as setting it up to "play" my Twitter feed, but the logical extension is to open it up to any data format, allowing the user to listen to the "soundtrack" of that data stream.

This is a work in progress.

A video demo can be seen here: http://www.youtube.com/watch?v=GYnPXLpNKlE

The sounds themselves were generated using the Sound eXchange open source sound processing utility:
http://sox.sourceforge.net/
