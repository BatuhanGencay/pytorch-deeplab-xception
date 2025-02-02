from __future__ import print_function, division
import os
from PIL import Image
import numpy as np
from torch.utils.data import Dataset
from mypath import Path
from torchvision import transforms
from dataloaders import custom_transforms as tr

class RiceSegmentation(Dataset):

    NUM_CLASSES = 4
    
    def __init__(self,
                 args,
                 base_dir=Path.db_root_dir('rice'),
                 split='train',
                 ):
        super().__init__()
        self._base_dir = base_dir
        self._image_dir = os.path.join(self._base_dir, 'label')
        self._mask_dir = os.path.join(self._base_dir, 'mask')
        self.TOTAL_SAMPLES = 736
        self.args = args
        self.split = split
        split_index = self.TOTAL_SAMPLES//5

        if split == 'train':
            self.images = os.listdir(self._image_dir)[split_index:]
            self.masks = os.listdir(self._mask_dir)[split_index:]
        else:
            self.images = os.listdir(self._image_dir)[:split_index]
            self.masks = os.listdir(self._mask_dir)[:split_index]


        # Display stats
        print('Number of images in {}: {:d}'.format(split, len(self.images)))

    def __len__(self):
        return len(self.images)


    def __getitem__(self, index):
        _img, _target = self._make_img_gt_point_pair(index)
        sample = {'image': _img, 'label': _target}

        if self.split == "train":           
            return self.transform_tr(sample)
        elif self.split == 'val':
            return self.transform_val(sample)


    def _make_img_gt_point_pair(self, index):
        _img = Image.open(self._image_dir + '/'+ self.images[index]).convert('RGB')
        _target = Image.open(self._mask_dir + '/' +self.masks[index])
        img_np = np.array(_target)
        mask = np.sum(img_np,2)/255
        # print(mask.shape)
        return _img, Image.fromarray(mask)

    def transform_tr(self, sample):
        composed_transforms = transforms.Compose([
            tr.RandomHorizontalFlip(),
            tr.RandomScaleCrop(base_size=self.args.base_size, crop_size=self.args.crop_size),
            tr.RandomGaussianBlur(),
            tr.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
            tr.ToTensor()])

        return composed_transforms(sample)

    def transform_val(self, sample):

        composed_transforms = transforms.Compose([
            tr.FixScaleCrop(crop_size=self.args.crop_size),
            tr.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
            tr.ToTensor()])

        return composed_transforms(sample)

    def __str__(self):
        return 'RICE2(split=' + str(self.split) + ')'


if __name__ == '__main__':
    from dataloaders.utils import decode_segmap
    from torch.utils.data import DataLoader
    import matplotlib.pyplot as plt
    import argparse

    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    args.base_size = 512
    args.crop_size = 256

    voc_train = VOCSegmentation(args, split='train')

    dataloader = DataLoader(voc_train, batch_size=5, shuffle=True, num_workers=0)

    for ii, sample in enumerate(dataloader):
        for jj in range(sample["image"].size()[0]):
            img = sample['image'].numpy()
            gt = sample['label'].numpy()
            tmp = np.array(gt[jj]).astype(np.uint8)
            segmap = decode_segmap(tmp, dataset='pascal')
            img_tmp = np.transpose(img[jj], axes=[1, 2, 0])
            img_tmp *= (0.229, 0.224, 0.225)
            img_tmp += (0.485, 0.456, 0.406)
            img_tmp *= 255.0
            img_tmp = img_tmp.astype(np.uint8)
            plt.figure()
            plt.title('display')
            plt.subplot(211)
            plt.imshow(img_tmp)
            plt.subplot(212)
            plt.imshow(segmap)

        if ii == 1:
            break

    plt.show(block=True)


