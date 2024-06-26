from mmpretrain import ImageClassificationInferencer
import torch
from mmengine.config import Config
import numpy as np

# for classification of healthy or unhealthy
model = 'swin'
schedule = 'lr_decr'
epoch = '100'
method = 'ros25_aug_pretrained_focal2'

# for phase 1
#model_config = f'../config/phase1/{model}_sgd0_01.py'
#model_pretrained = f'../work_dirs/phase1/{model}/{schedule}/epoch_{epoch}.pth'

# for phase 2/3
model_config = f'../config/phase3/{model}_{method}.py'
model_pretrained = f'../work_dirs/phase3/{model}/{method}/{schedule}/epoch_{epoch}.pth'

out_path = f'../../utils/correct/{model}_{method}_{schedule}.txt'

cfg = Config.fromfile(model_config)
model = ImageClassificationInferencer(model = model_config, pretrained = model_pretrained)

paths, labels = [], []

with open("../../B_E_P_N/meta/test.txt", "r") as file:
    for line in file:
        path, label = line.strip().split(" ", 1)
        label = int(label)
        if label == 1 or label == 3:
            paths.append(f'{path}')
            labels.append(label)

polyps = []
esophagitis = []

for label, path in zip(labels, paths):
    res = model(path)[0]
    if res['pred_label'] == label:
        if label == 1:
            polyps.append(path)
        if label == 3:
            esophagitis.append(path)

with open(out_path, 'a') as file:
    file.write(f"\n\nCorrect Predictions \n Algorithm: {method} with Model: {model} with schedule: {schedule} \n")
    file.write('Polyps: \n')
    for pol in polyps:
        file.write(f'{pol}, ')
    file.write('\nEsophagitis \n')
    for eso in esophagitis:
        file.write(f'{eso}, ')

