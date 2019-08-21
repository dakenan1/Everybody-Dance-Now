import os
import imageio
from PIL import Image

T = 10
#reader = imageio.get_reader('video.avi','ffmpeg')
reader = imageio.get_reader('mv_test.mp4','ffmpeg')
for i, im in enumerate(reader):
    if (i%T ==0):
        x = i/T
    #imageio.imwrite(str(i)+'.png',im[:, :, 1])
    	#print('i===',i)
    	#print('im===',im)
        imageio.imwrite('/home/aa/Desktop/everybody_dance_now_pytorch/datasets/train/train_B/'+ '%05d' % x + '.png',im[:, :, :])


