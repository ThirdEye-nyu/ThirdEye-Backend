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

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

class SingletonClass(object):
  def __new__(cls):
    if not hasattr(cls, 'instance'):
      cls.instance = super(SingletonClass, cls).__new__(cls)
    return cls.instance

class Predictor(SingletonClass):


    def __init__(self):
        self.device = patchcore.utils.set_torch_device([])
        self.nn_method = patchcore.common.FaissNN(False, 0)
        self.patchcore_instance = patchcore.patchcore.PatchCore(self.device)
        self.patch_core_path = "/app/models/MVTecAD_Results/IM224_WR50_L2-3_P01_D1024-1024_PS-3_AN-1_S0_9/models/mvtec_toothbrush"
        self.patchcore_instance.load_from_path(
            load_path=self.patch_core_path, device=self.device, nn_method=self.nn_method
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
        for i in range(10):
            image = self.image_loader(
                "/app/data/toothbrush/test/good/00" + str(i) + ".png")
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
