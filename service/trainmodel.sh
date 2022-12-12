datapath="/Users/jaikar/Documents/NYU/Networks/mvtec"
datasets=('toothbrush')
dataset_flags=($(for dataset in "${datasets[@]}"; do echo '-d '"${dataset}"; done))

############# Detection
### IM224:
# Baseline: Backbone: WR50, Blocks: 2 & 3, Coreset Percentage: 10%, Embedding Dimensionalities: 1024 > 1024, neighbourhood aggr. size: 3, neighbours: 1, seed: 0
# Performance: Instance AUROC: 0.992, Pixelwise AUROC: 0.981, PRO: 0.944
python bin/run_patchcore.py --seed 0 --save_patchcore_model --save_segmentation_images --log_group IM224_WR50_L2-3_P01_D1024-1024_PS-3_AN-1_S0 --log_project MVTecAD_Results results \
patch_core -b wideresnet50 -le layer2 -le layer3 --pretrain_embed_dimension 1024  --target_embed_dimension 1024 --anomaly_scorer_num_nn 1 --patchsize 3 sampler -p 0.1 approx_greedy_coreset dataset --resize 256 --imagesize 224 "${dataset_flags[@]}" mvtec $datapath