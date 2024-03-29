import torch 
from torch.utils.data import Dataset
from torchvision.transforms import ToTensor

import os 
import pandas as pd
from PIL import Image

class Gastro_Dataset(Dataset):

    def __init__(self, annotations_file, img_dir, transform = None, target_transform=None):
        self.img_labels = pd.read_csv(annotations_file, sep = ' ')
        self.img_dir = img_dir
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.img_labels)

    def __getitem__(self, idx):
        img_path = os.path.join(self.img_dir, self.img_labels.iloc[idx, 0])
        image = Image.open(img_path).convert('RGB')
        r, g, b = image.split()

        # Merge the channels to form a BGR image
        #image = Image.merge("RGB", (b, g, r))
        label = self.img_labels.iloc[idx, 1]
        if self.transform:
            image = self.transform(image)
        if self.target_transform:
            label = self.target_transform(label)
        return image, label 
