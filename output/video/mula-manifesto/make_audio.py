"""Original instrumental bed and transition cues for the Mula manifesto."""
from pathlib import Path
import wave
import numpy as np

root = Path(__file__).resolve().parent
rate = 48000
duration = 65
sound = np.zeros((rate * duration, 2), dtype=np.float64)
rng = np.random.default_rng(20261027)

def add(start, samples, volume=1.0, pan=0.0):
    offset = int(start * rate)
    if offset < 0 or offset >= len(sound):
        return
    count = min(len(samples), len(sound) - offset)
    sound[offset:offset+count, 0] += samples[:count] * volume * np.sqrt((1-pan)/2)
    sound[offset:offset+count, 1] += samples[:count] * volume * np.sqrt((1+pan)/2)

def note(start, freq, length, volume, pan=0):
    t = np.arange(int(length*rate))/rate
    envelope = (1-np.exp(-t*60))*np.exp(-t*2.3)*np.minimum(1,(length-t)*10)
    tone = np.sin(2*np.pi*freq*t) + 0.28*np.sin(2*np.pi*freq*2*t) + 0.08*np.sin(2*np.pi*freq*3*t)
    add(start, tone*envelope, volume, pan)

chords = [[146.83,174.61,220.0],[116.54,146.83,174.61],[130.81,174.61,220.0],[130.81,164.81,196.0]]
for block in range(14):
    start = block*4.0
    chord = chords[block%4]
    for i,f in enumerate(chord):
        t=np.arange(int(4.4*rate))/rate
        env=np.minimum(t/0.9,1)*np.minimum((4.4-t)/1.1,1)
        pad=(np.sin(2*np.pi*f*t)+0.3*np.sin(2*np.pi*(f*1.002)*t))*env
        add(start,pad,0.025,(i-1)*0.5)
    for i in range(4):
        note(start+i*0.75,chord[i%3]*2,2.2,0.06,0.3*np.sin(i))

beat=60/112
for n,start in enumerate(np.arange(16,56,beat)):
    t=np.arange(int(0.3*rate))/rate
    kick=np.sin(2*np.pi*(48*t+4*(1-np.exp(-t*32))))*np.exp(-t*17)
    add(float(start),kick,0.23)
    if n%2==1:
        noise=rng.normal(0,1,int(0.13*rate))
        tt=np.arange(len(noise))/rate
        add(float(start),noise*np.exp(-tt*38),0.055,-0.15)
    for delay in [0,beat/2]:
        noise=rng.normal(0,1,int(0.045*rate))
        noise=np.concatenate([[0],np.diff(noise)])
        tt=np.arange(len(noise))/rate
        add(float(start+delay),noise*np.exp(-tt*95),0.018,0.4)
    chord=chords[int((start-16)/4)%4]
    note(float(start),chord[n%3]*4,0.7,0.055,np.sin(n)*0.55)

# Soft manual-process clicks, restrained telephone pulse, and transition accents.
for start in [9.0,10.3,11.6]:
    t=np.arange(int(0.06*rate))/rate
    add(start,rng.normal(0,1,len(t))*np.exp(-t*100),0.07)
for start in [9.05,9.3]:
    t=np.arange(int(0.14*rate))/rate
    add(start,(np.sin(2*np.pi*440*t)+np.sin(2*np.pi*480*t))*np.sin(np.pi*t/0.14)**2,0.035)
for end in [16,22,40,44]:
    t=np.arange(rate)/rate
    noise=rng.normal(0,1,len(t))
    smooth=np.convolve(noise,np.ones(30)/30,mode='same')
    add(end-1,smooth*(t**2),0.2)
    note(end,73.415,2.3,0.18)
# Pause before the final invitation, then a short resolved closing chord.
for i,f in enumerate([130.81,174.61,220,349.23]):
    note(61+i*0.06,f,3.8,0.075,(i-1.5)*0.25)
fade=np.ones(len(sound))
fade[:rate]=np.linspace(0,1,rate)
fade[-rate:]=np.linspace(1,0,rate)
sound*=fade[:,None]
peak=np.max(np.abs(sound))
if peak>0:
    sound*=0.84/peak
pcm=(np.clip(sound,-1,1)*32767).astype('<i2')
with wave.open(str(root/'soundtrack.wav'),'wb') as out:
    out.setnchannels(2)
    out.setsampwidth(2)
    out.setframerate(rate)
    out.writeframes(pcm.tobytes())
print(f'Original soundtrack: {duration}s, stereo, {rate}Hz, peak {np.max(np.abs(sound)):.3f}')
