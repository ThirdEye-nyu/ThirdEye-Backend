import contextlib
import gc
import logging
import os
import sys

import click
import numpy as np
import torch

import patchcore.common
import patchcore.metrics
import patchcore.patchcore
import patchcore.sampler
import patchcore.utils
from PIL import Image
import torch
from torchvision import transforms
from PyNomaly import loop
import time
import glob
from service.run_patchcore import patch_core,dataset,run,sampler
from service.config import *

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class Predictor(object):


    def __init__(self, line_id):
        self.line_id = line_id
        self.model_path =  os.path.join(MODELS_FOLDER, str(line_id))
        if not os.path.isdir(self.model_path ):
            os.mkdir(self.model_path )
        self.defects_path = os.path.join(DEFECTS_FOLDER, str(line_id))
        if not os.path.isdir(self.defects_path ):
            os.mkdir(self.defects_path )
        self.data_path = os.path.join(DATA_FOLDER, str(line_id))
        self.device = patchcore.utils.set_torch_device([])
        self.nn_method = patchcore.common.FaissNN(False, 0)
        self.patchcore_instance = patchcore.patchcore.PatchCore(self.device)
        self.patchcore_instance.load_from_path(
            load_path=self.model_path, device=self.device, nn_method=self.nn_method
        )
        # self.model = patchcore_instance

        transform_img = [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
        self.loader = transforms.Compose(transform_img)
        images = []
        good_images_list = glob.glob(self.data_path + "/test/good/*.png")
        for i in good_images_list[:10]:
            image = self.image_loader(i)
            image = image.squeeze()
            images.append(image)

        images = torch.stack(images)
        scores, masks = self.patchcore_instance._predict(images)
        self.scores = scores

    def image_loader(self, img_path):
        """load image, returns cuda tensor"""
        image = Image.open(img_path)
        image = self.loader(image).float()
        image = image.unsqueeze(0)
        return image

    def predict(self, img_path):
        device = patchcore.utils.set_torch_device([])
        nn_method = patchcore.common.FaissNN(False, 1)
        patchcore_instance = patchcore.patchcore.PatchCore(device)
        patch_core_path = "/app/models/MVTecAD_Results/IM224_WR50_L2-3_P01_D1024-1024_PS-3_AN-1_S0_9/models/mvtec_toothbrush"
        patchcore_instance.load_from_path(
            load_path=patch_core_path, device=device, nn_method=nn_method
        )
        model = patchcore_instance
        image = self.image_loader(img_path)
        start_time = int(time.time())
        preds, masks = model._predict(image)
        pred_scores = self.scores + preds
        m = loop.LocalOutlierProbability(np.array(pred_scores)).fit()
        prob_scores = m.local_outlier_probabilities
        confidence = prob_scores[-1]
        pred_class = "Defective" if confidence > 0.5 else "Good"
        confidence = 1 - confidence
        pred_time = int(time.time()) - start_time
        return {"class": pred_class, "good_probability": confidence, "time_taken" : pred_time}


    def predict_batch(self, test_dir):
        image_paths = glob.glob(test_dir + "/*")
        images =[]
        for i in image_paths:
            image = self.image_loader(i)
            image = image.squeeze()
            images.append(image)
        images = torch.stack(images)
        scores, masks = self.patchcore_instance._predict(images)

        defective_image_paths = []
        defective_image_scores = []
        defective_image_masks = []

        for i in range(len(scores)):
            score = scores[i]
            mask = masks[i]
            pred_scores = self.scores + [score]
            m = loop.LocalOutlierProbability(np.array(pred_scores)).fit()
            prob_scores = m.local_outlier_probabilities
            confidence = prob_scores[-1]
            if confidence > 0.5:
                print("defective image found %s " %image_paths[i])
                defective_image_paths.append(image_paths[i])
                defective_image_scores.append(score)
                defective_image_masks.append(mask)
        
        self.plot_defective_images(self.defects_path, defective_image_paths,defective_image_scores,defective_image_masks)
        
        return defective_image_paths


    def plot_defective_images(self,defects_save_path, defective_image_paths,defective_image_scores,defective_image_masks):
        if len(defective_image_paths) > 0:
            scores = np.array(defective_image_scores)
            segmentations = np.array(defective_image_masks)
            min_scores = (
                segmentations.reshape(len(segmentations), -1)
                .min(axis=-1)
                .reshape(-1, 1, 1, 1)
            )
            max_scores = (
                segmentations.reshape(len(segmentations), -1)
                .max(axis=-1)
                .reshape(-1, 1, 1, 1)
            )
            segmentations = (segmentations - min_scores) / (max_scores - min_scores)
            segmentations = np.mean(segmentations, axis=0)

            image_save_path = defects_save_path
            os.makedirs(image_save_path, exist_ok=True)

            def image_transform(image):
                return np.array(image).transpose(2, 0, 1)

            mask_paths = [None]*len(defective_image_paths)

            patchcore.utils.plot_segmentation_images(
                image_save_path,
                defective_image_paths,
                defective_image_masks,
                defective_image_scores,
                image_transform=image_transform,
                mask_paths=mask_paths
            )






        





    
