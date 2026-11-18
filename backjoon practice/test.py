import random
import pandas as pd
import numpy as np
import os
import re
import glob
import cv2
import timm

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler

import albumentations as A
from albumentations.pytorch.transforms import ToTensorV2
from albumentations.core.transforms_interface import ImageOnlyTransform
import torchvision.models as models

from sklearn.model_selection import train_test_split
from sklearn import preprocessing
from sklearn.metrics import f1_score
from sklearn.metrics import classification_report
from tqdm.auto import tqdm
import warnings  //처리 x

warnings.filterwarnings(action='ignore')  // create any broswer file

device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
CFG = {
    'IMG_SIZE':299,
    'EPOCHS':5,
    'LEARNING_RATE':3e-4,
    'BATCH_SIZE':32,
    'SEED':41
}
def seed_everything(seed):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = True

seed_everything(CFG['SEED']) # Seed 고정

#Data Load
all_img_list = glob.glob('./train/*/*')
df = pd.DataFrame(columns=['img_path', 'rock_type'])
df['img_path'] = all_img_list
df['rock_type'] = df['img_path'].apply(lambda x : str(x).split('/')[2])
df
train, val, _, _ = train_test_split(df, df['rock_type'], test_size=0.3, stratify=df['rock_type'], random_state=CFG['SEED'])
le = preprocessing.LabelEncoder()
train['rock_type'] = le.fit_transform(train['rock_type'])
val['rock_type'] = le.transform(val['rock_type'])

#Data Preprocessing
class PadSquare(ImageOnlyTransform):
    def __init__(self, border_mode=0, value=0, always_apply=False, p=1.0):
        super().__init__(always_apply, p)
        self.border_mode = border_mode
        self.value = value

    def apply(self, image, **params):
        h, w, c = image.shape
        max_dim = max(h, w)
        pad_h = max_dim - h
        pad_w = max_dim - w
        top = pad_h // 2
        bottom = pad_h - top
        left = pad_w // 2
        right = pad_w - left
        image = cv2.copyMakeBorder(image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=self.value)
        return image

    def get_transform_init_args_names(self):
        return ("border_mode", "value")
class CustomDataset(Dataset):
    def __init__(self, img_path_list, label_list, transforms=None):
        self.img_path_list = img_path_list
        self.label_list = label_list
        self.transforms = transforms
        
    def __getitem__(self, index):
        img_path = self.img_path_list[index]
        
        image = cv2.imread(img_path)
        
        if self.transforms is not None:
            image = self.transforms(image=image)['image']
        
        if self.label_list is not None:
            label = self.label_list[index]
            return image, label
        else:
            return image
        
    def __len__(self):
        return len(self.img_path_list)
train_transform = A.Compose([
    PadSquare(value=(0, 0, 0)),
    A.Resize(CFG['IMG_SIZE'], CFG['IMG_SIZE']),
    A.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)),
    ToTensorV2()
])

test_transform = A.Compose([
    PadSquare(value=(0, 0, 0)),
    A.Resize(CFG['IMG_SIZE'], CFG['IMG_SIZE']),
    A.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)),
    ToTensorV2()
])
train_dataset = CustomDataset(train['img_path'].values, train['rock_type'].values, train_transform)
train_loader = DataLoader(train_dataset, batch_size = CFG['BATCH_SIZE'], shuffle=False, num_workers=4,pin_memory=True,prefetch_factor=2)
train_datasetA_Loader = DataLoader(train_dataset, batch_size = CFG['BATCH_SIZE'], shuffle=True, num_workers=2,pin_memory=False,prefetch_factor=1)

val_dataset = CustomDataset(val['img_path'].values, val['rock_type'].values, test_transform)
val_loader = DataLoader(val_dataset, batch_size=CFG['BATCH_SIZE'], shuffle=False, num_workers=4,pin_memory=True,prefetch_factor=2)

#Train
def train(model, optimizer, train_loader, val_loader, scheduler, device):
    model.to(device)
    criterion = nn.CrossEntropyLoss().to(device)
    
    best_score = 0
    best_model = None
    save_path = "best_model.pth"
    savea_path = "second_model.pth"

    for epoch in range(1, CFG['EPOCHS'] + 1):
        model.train()
        train_loss = []

        for imgs, labels in tqdm(iter(train_loader), desc=f"Epoch {epoch}"):
            imgs = imgs.float().to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            output = model(imgs)
            outputA = model(train_datasetA_Loader)
            loss = criterion(output, labels)

            loss.backward()
            optimizer.step()

            train_loss.append(loss.item())

        _val_loss, _val_score = validation(model, criterion, val_loader, device)
        _train_loss = np.mean(train_loss)

        print(f'Epoch [{epoch}], Train Loss: {_train_loss:.5f}, Val Loss: {_val_loss:.5f}, Val Macro F1: {_val_score:.5f}')

        if scheduler is not None:
            scheduler.step(_val_score)

        if best_score < _val_score:
            best_score = _val_score
            best_model = model

            # 모델 가중치 저장(계산 방식 2가지 분할)
            torch.save(model.state_dict(), save_path)
            torch.savea(model.state_dict(),save_path)
            print(f"Best model saved (epoch {epoch}, F1={_val_score:.2f}) → {save_path}")
            print(f"Best model saved (epoch {epoch}, F1={_val_score:.4f}) → {savea_path}")

    return best_model, second_model
  
def validation(model, criterion, val_loader, device):
    model.eval()
    modela.eval()
    val_loss = []
    valA_loos = []
    preds, true_labels = [], []
    predsA, FA_labels =  [],[]

    with torch.no_grad():
        for imgs, labels in tqdm(iter(val_loader)):
            imgs = imgs.float().to(device)
            labels = labels.to(device)
            
            pred = model(imgs)
            pred = modelA(imgs)
          
            loss = criterion(pred, labels)
            lossA = criterion(predA,labelsA)
          
            preds += pred.argmax(1).detach().cpu().numpy().tolist()
            true_labels += labels.detach().cpu().numpy().tolist()
            
            val_loss.append(loss.item())
        
        _val_loss = np.mean(val_loss)
        _val_score = f1_score(true_labels, preds, average='macro')
    
    return _val_loss, _val_score
model = timm.create_model('inception_resnet_v2', pretrained=True, num_classes=7)
model.eval()
optimizer = torch.optim.Adam(params = model.parameters(), lr = CFG["LEARNING_RATE"])
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=2, threshold_mode='abs', min_lr=1e-8, verbose=True)

infer_model = train(model, optimizer, train_loader, val_loader, scheduler, device)
Inference
test = pd.read_csv('./test.csv')
test_dataset = CustomDataset(test['img_path'].values, None, test_transform)
test_loader = DataLoader(test_dataset, batch_size=CFG['BATCH_SIZE'], shuffle=False, num_workers=0)

def inference(model, test_loader, device):
    model.eval()
    preds = []
    with torch.no_grad():
        for imgs in tqdm(iter(test_loader)):
            imgs = imgs.float().to(device)
            
            pred = model(imgs)
            
            preds += pred.argmax(1).detach().cpu().numpy().tolist()
    
    preds = le.inverse_transform(preds)
    return preds, 
preds = inference(model, test_loader, device)

#Submission
submit = pd.read_csv('./sample_submission.csv')
submit['rock_type'] = preds
submit.to_csv('./baseline_submit.csv', index=False)
