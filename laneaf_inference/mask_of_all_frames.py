import os
import json
from datetime import datetime
import argparse
from torchvision import transforms as tf

import numpy as np
import cv2

import torch
from models.dla.pose_dla_dcn import get_pose_net
from models.erfnet.erfnet import ERFNet
from models.enet.ENet import ENet
from utils.affinity_fields import decodeAFs
from utils.visualize import tensor2image, create_viz
import numpy as np
from matplotlib import pyplot as plt
import time
from tqdm import tqdm  # Import tqdm for progress bar

start_time = time.time()

parser = argparse.ArgumentParser('Options for inference with LaneAF models in PyTorch...')
parser.add_argument('--snapshot', type=str, default=None, help='path to pre-trained model snapshot')
parser.add_argument('--seed', type=int, default=1, help='set seed to some constant value to reproduce experiments')
parser.add_argument('--no-cuda', action='store_true', default=False, help='do not use cuda for training')
parser.add_argument('--save-viz', action='store_true', default=False, help='save visualization depicting intermediate and final results')
parser.add_argument('--video-path', type=str, default=None, help='path to the input video')
parser.add_argument('--output-dir', type=str, default='output', help='directory to save the output frames')

args = parser.parse_args()

# Setup args
args.cuda = not args.no_cuda and torch.cuda.is_available()

# Load the model
heads = {'hm': 1, 'vaf': 2, 'haf': 1}
model = get_pose_net(num_layers=34, heads=heads, head_conv=256, down_ratio=4)  # Modify this based on your model architecture
model.load_state_dict(torch.load(args.snapshot, map_location=torch.device('cpu')))

if args.cuda:
    model.cuda()
model.eval()

# Ensure output directory exists
os.makedirs("masks_of_all_frames", exist_ok=True)

# Open video
cap = cv2.VideoCapture("/content/drive/MyDrive/TC_00048cropped.MP4")
frame_idx = 0

# Get total number of frames in video for tqdm
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Initialize tqdm
pbar = tqdm(total=total_frames, desc='Processing frames')

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    img = frame.astype(np.float32) / 255.
    img = cv2.resize(img[:, :, :], (1664, 576), interpolation=cv2.INTER_LINEAR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_transforms = tf.Compose([
        tf.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    img_input = img_transforms(torch.from_numpy(img).permute(2, 0, 1).contiguous().float())
    img_input = img_input.unsqueeze(0)

    img = img_input.cuda() if args.cuda else img_input

    # Do the forward pass
    outputs = model(img)[-1]

    img = tensor2image(img.detach(), np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225]))
    mask_out = tensor2image(torch.sigmoid(outputs['hm']).repeat(1, 3, 1, 1).detach(),
        np.array([0.0 for i in range(3)], dtype='float32'), np.array([1.0 for i in range(3)], dtype='float32'))
    vaf_out = np.transpose(outputs['vaf'][0, :, :, :].detach().cpu().float().numpy(), (1, 2, 0))
    haf_out = np.transpose(outputs['haf'][0, :, :, :].detach().cpu().float().numpy(), (1, 2, 0))

    # Decode AFs to get lane instances
    seg_out = decodeAFs(mask_out[:, :, 0], vaf_out, haf_out, fg_thresh=128, err_thresh=5)

    cv2.imwrite(os.path.join(args.output_dir, f'/content/drive/MyDrive/LaneAF/masks_of_all_frames/frame_{frame_idx:06d}_seg.png'), cv2.resize(seg_out, (1664,576), interpolation=cv2.INTER_NEAREST))
    
    frame_idx += 1
    pbar.update(1)  # Update tqdm progress bar

cap.release()
pbar.close()  # Close tqdm progress bar
print('Inference done.')
end_time = time.time()
execution_time = end_time - start_time
print(f'Total execution time: {execution_time} seconds')







