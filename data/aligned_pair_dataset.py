### Copyright (C) 2017 NVIDIA Corporation. All rights reserved. 
### Licensed under the CC BY-NC-SA 4.0 license (https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode).
import os.path
from data.base_dataset import BaseDataset, get_params, get_transform, normalize
from data.image_folder import make_dataset
from PIL import Image
import PIL 
import torch

'''
 __getitem__ returns N consecutive frames 
 along with correspondingposes as a training sample.
 For training: N=2
 For testing: N can be arbitrary length
'''


class AlignedPairDataset(BaseDataset):
    def initialize(self, opt):
        self.opt = opt
        self.root = opt.dataroot    

        ### input A (label maps)
        dir_A = '_A' if self.opt.label_nc == 0 else '_label'
        self.dir_A = os.path.join(opt.dataroot, opt.phase + dir_A)
        self.A_paths = sorted(make_dataset(self.dir_A))

        ### input B (real images)
        #if opt.isTrain:
        dir_B = '_B' if self.opt.label_nc == 0 else '_img'
        self.dir_B = os.path.join(opt.dataroot, opt.phase + dir_B)
        self.B_paths = sorted(make_dataset(self.dir_B))

        ### instance maps
        if not opt.no_instance:
            self.dir_inst = os.path.join(opt.dataroot, opt.phase + '_inst')
            self.inst_paths = sorted(make_dataset(self.dir_inst))

        ### load precomputed instance-wise encoded features
        if opt.load_features:                              
            self.dir_feat = os.path.join(opt.dataroot, opt.phase + '_feat')
            print('----------- loading features from %s ----------' % self.dir_feat)
            self.feat_paths = sorted(make_dataset(self.dir_feat))

        self.dataset_size = len(self.A_paths)

        ### define clip length
        if opt.isTrain:
            self.clip_length = 2
        else:
            self.clip_length = min(opt.clip_length, len(self.A_paths))
        print(len(self.A_paths), self.clip_length)

    def __getitem__(self, index):        
        ### input A (label maps)
        if index > self.dataset_size - self.clip_length:
            index = 0  # it's a rare chance and won't be effecting training dynamics

        A_path = self.A_paths[index: index + self.clip_length]

        A = [Image.open(path) for path in A_path]
        '''       
        A = []
        for path in A_path:
            with open(path,'rb') as i: 
                img = Image.open(i)
                #print('img===',img)
                A.append(img)
        print('A====',A)
        '''
        params = get_params(self.opt, A[0].size)
        if self.opt.label_nc == 0:
            transform_A = get_transform(self.opt, params)
            A_tensor = [transform_A(item.convert('RGB')) for item in A]
            A_tensor = torch.stack(A_tensor, dim=0)
        else:
            transform_A = get_transform(self.opt, params, method=Image.NEAREST, normalize=False)
            A_tensor = transform_A(A) * 255.0

        B_tensor = inst_tensor = feat_tensor = 0
        ### input B (real images)
        if self.opt.isTrain:
            B_path = self.B_paths[index: index + self.clip_length]
            B = [Image.open(path).convert('RGB') for path in B_path]
            transform_B = get_transform(self.opt, params)      
            B_tensor = [transform_B(item) for item in B]
            B_tensor = torch.stack(B_tensor, dim=0)
        else: # only retain first frame for testing
            B_path = self.B_paths[index]
            B = Image.open(B_path).convert('RGB')
            transform_B = get_transform(self.opt, params)
            B_tensor = transform_B(B)

        ### if using instance maps (which is never supposed to)
        if not self.opt.no_instance:
            inst_path = self.inst_paths[index: index + self.clip_length]
            inst = [Image.open(path) for path in inst_path]
            inst_tensor = [transform_A(item) for item in inst]
            inst_tensor = torch.stack(inst_tensor, dim=0)

            if self.opt.load_features:
                feat_path = self.feat_paths[index: index + self.clip_length]
                feat = [Image.open(path).convert('RGB') for path in feat_path]
                norm = normalize()
                feat_tensor = [norm(transform_A(item)) for item in feat]
                feat_tensor = torch.stack(feat_tensor, dim=0)

        input_dict = {'label': A_tensor, 'inst': inst_tensor, 'image': B_tensor, 
                      'feat': feat_tensor, 'path': A_path}

        return input_dict

    def __len__(self):
        return len(self.A_paths) // self.opt.batchSize * self.opt.batchSize

    def name(self):
        return 'AlignedPairDataset'
