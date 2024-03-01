#!/bin/bash

cd ..

python train.py ../config/phase_1/resnet50_sgd0_01.py --work-dir ../work_dirs/phase_1/resnet50/lr_0.01/

python train.py ../config/phase_1/resnet50_sgd0_001.py --work-dir ../work_dirs/phase_1/resnet50/lr_0.001/

python train.py ../config/phase_1/resnet50_sgd_decr.py --work-dir ../work_dirs/phase_1/resnet50/lr_decr/
