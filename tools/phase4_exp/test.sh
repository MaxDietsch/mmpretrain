#!/bin/bash

cd ..

method="128"
model="efficientnet_b4"
epoch="91 92 93 94 95 96 97 98 99 100"
lr_array=("lr_0.01" "lr_0.001" "lr_decr")
#epoch_lr0_01="60 98"
#epoch_lr0_001="68 100"
#epoch_lr_decr="60 62 94"

#epochs=("$epoch_lr0_01" "$epoch_lr0_001" "$epoch_lr_decr")
epochs=("$epoch" "$epoch" "$epoch")

# iterate over outer array
for i in "${!epochs[@]}"
do
    IFS=' ' read -r -a innerArray <<< "${epochs[$i]}"
    # Iterate over inner array of integers
    for j in "${!innerArray[@]}"
    do
        epoch="${innerArray[$j]}"

        python test.py ../config/phase4/${model}_test.py ../work_dirs/phase4/${model}/${method}/${lr_array[$i]}/epoch_"$epoch".pth --work-dir ../work_dirs/phase4/${model}/test/${method}/${lr_array[$i]}/epoch_"$epoch"

    done
done
