import contextlib
import logging
import os
import sys

import click
import numpy as np
import torch

import patchcore.backbones
import patchcore.common
import patchcore.metrics
import patchcore.patchcore
import patchcore.sampler
import patchcore.utils

LOGGER = logging.getLogger(__name__)

_DATASETS = {"mvtec": ["patchcore.datasets.mvtec", "MVTecDataset"]}




def run(
    methods,
    models_path,
    defects_path,
    gpu=[],
    seed=0,
    save_segmentation_images=True,
    save_patchcore_model=True,
):
    # methods = {key: item for (key, item) in methods}

    run_save_path = models_path

    list_of_dataloaders = methods["get_dataloaders"]

    device = patchcore.utils.set_torch_device([])
    # Device context here is specifically set and used later
    # because there was GPU memory-bleeding which I could only fix with
    # context managers.
    device_context = (
        torch.device("cuda:{}".format(device.index))
        if "cuda" in device.type.lower()
        else contextlib.suppress()
    )

    result_collect = []

    for dataloader_count, dataloaders in enumerate(list_of_dataloaders):
        LOGGER.info(
            "Evaluating dataset [{}] ({}/{})...".format(
                dataloaders["training"].name,
                dataloader_count + 1,
                len(list_of_dataloaders),
            )
        )

        patchcore.utils.fix_seeds(seed, device)

        dataset_name = dataloaders["training"].name

        with device_context:
            # torch.empty_cache()
            imagesize = dataloaders["training"].dataset.imagesize
            sampler = methods["get_sampler"]
            PatchCore_list = methods["get_patchcore"]
            if len(PatchCore_list) > 1:
                LOGGER.info(
                    "Utilizing PatchCore Ensemble (N={}).".format(len(PatchCore_list))
                )
            for i, PatchCore in enumerate(PatchCore_list):
                # torch.empty_cache()
                if PatchCore.backbone.seed is not None:
                    patchcore.utils.fix_seeds(PatchCore.backbone.seed, device)
                LOGGER.info(
                    "Training models ({}/{})".format(i + 1, len(PatchCore_list))
                )
                # torch.empty_cache()
                PatchCore.fit(dataloaders["training"])

            # torch.empty_cache()
            aggregator = {"scores": [], "segmentations": []}
            for i, PatchCore in enumerate(PatchCore_list):
                # torch.empty_cache()
                LOGGER.info(
                    "Embedding test data with models ({}/{})".format(
                        i + 1, len(PatchCore_list)
                    )
                )
                scores, segmentations, labels_gt, masks_gt = PatchCore.predict(
                    dataloaders["testing"]
                )
                aggregator["scores"].append(scores)
                aggregator["segmentations"].append(segmentations)

            scores = np.array(aggregator["scores"])
            min_scores = scores.min(axis=-1).reshape(-1, 1)
            max_scores = scores.max(axis=-1).reshape(-1, 1)
            scores = (scores - min_scores) / (max_scores - min_scores)
            scores = np.mean(scores, axis=0)

            segmentations = np.array(aggregator["segmentations"])
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

            anomaly_labels = [
                x[1] != "good" for x in dataloaders["testing"].dataset.data_to_iterate
            ]

            
            if save_patchcore_model:
                patchcore_save_path = run_save_path
                LOGGER.info("Saving model to {0}".format(patchcore_save_path))
                os.makedirs(patchcore_save_path, exist_ok=True)
                for i, PatchCore in enumerate(PatchCore_list):
                    prepend = (
                        "Ensemble-{}-{}_".format(i + 1, len(PatchCore_list))
                        if len(PatchCore_list) > 1
                        else ""
                    )
                    PatchCore.save_to_path(patchcore_save_path, prepend)

        LOGGER.info("\n\n-----\n")

def patch_core(
    sampler,
    backbone_names = ["wideresnet50"],
    layers_to_extract_from = ["layer2", "layer3"],
    pretrain_embed_dimension = 1024,
    target_embed_dimension=1024,
    preprocessing="mean",
    aggregation="mean",
    patchsize=3,
    patchscore="max",
    patchoverlap=0.0,
    anomaly_scorer_num_nn=1,
    patchsize_aggregate=[],
    faiss_on_gpu=True,
    faiss_num_workers=1,
    device='cpu',
    input_shape = [3,224,224]
    
):
    backbone_names = list(backbone_names)
    if len(backbone_names) > 1:
        layers_to_extract_from_coll = [[] for _ in range(len(backbone_names))]
        for layer in layers_to_extract_from:
            idx = int(layer.split(".")[0])
            layer = ".".join(layer.split(".")[1:])
            layers_to_extract_from_coll[idx].append(layer)
    else:
        layers_to_extract_from_coll = [layers_to_extract_from]

    loaded_patchcores = []
    for backbone_name, layers_to_extract_from in zip(
        backbone_names, layers_to_extract_from_coll
    ):
        backbone_seed = None
        if ".seed-" in backbone_name:
            backbone_name, backbone_seed = backbone_name.split(".seed-")[0], int(
                backbone_name.split("-")[-1]
            )
        backbone = patchcore.backbones.load(backbone_name)
        backbone.name, backbone.seed = backbone_name, backbone_seed

        nn_method = patchcore.common.FaissNN(faiss_on_gpu, faiss_num_workers)

        patchcore_instance = patchcore.patchcore.PatchCore(device)
        patchcore_instance.load(
            backbone=backbone,
            layers_to_extract_from=layers_to_extract_from,
            device=device,
            input_shape=input_shape,
            pretrain_embed_dimension=pretrain_embed_dimension,
            target_embed_dimension=target_embed_dimension,
            patchsize=patchsize,
            featuresampler=sampler,
            anomaly_scorer_num_nn=anomaly_scorer_num_nn,
            nn_method=nn_method,
        )
        loaded_patchcores.append(patchcore_instance)
    
    return loaded_patchcores



def sampler(name="approx_greedy_coreset", percentage=0.1, device='cpu'):
    if name == "identity":
        return patchcore.sampler.IdentitySampler()
    elif name == "greedy_coreset":
        return patchcore.sampler.GreedyCoresetSampler(percentage, device)
    elif name == "approx_greedy_coreset":
        return patchcore.sampler.ApproximateGreedyCoresetSampler(percentage, device)



def dataset(
    name="mvtec",
    data_path="",
    line_id="1",
    train_val_split=1,
    batch_size=2,
    resize=256,
    imagesize=224,
    num_workers=0,
    augment=True,
    seed =0
):
    dataset_info = _DATASETS[name]
    dataset_library = __import__(dataset_info[0], fromlist=[dataset_info[1]])

    dataloaders = []
    train_dataset = dataset_library.__dict__[dataset_info[1]](
        data_path,
        classname=line_id,
        resize=resize,
        train_val_split=1,
        imagesize=imagesize,
        split=dataset_library.DatasetSplit.TRAIN,
        seed=seed,
        augment=augment,
    )

    test_dataset = dataset_library.__dict__[dataset_info[1]](
        data_path,
        classname=line_id,
        resize=resize,
        imagesize=imagesize,
        split=dataset_library.DatasetSplit.TEST,
        seed=seed,
    )

    train_dataloader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    test_dataloader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
    )

    train_dataloader.name = name
    if line_id is not None:
        train_dataloader.name += "_" + line_id

        
    val_dataloader = None
    dataloader_dict = {
        "training": train_dataloader,
        "validation": val_dataloader,
        "testing": test_dataloader,
    }

    dataloaders.append(dataloader_dict)
    
    return dataloaders

