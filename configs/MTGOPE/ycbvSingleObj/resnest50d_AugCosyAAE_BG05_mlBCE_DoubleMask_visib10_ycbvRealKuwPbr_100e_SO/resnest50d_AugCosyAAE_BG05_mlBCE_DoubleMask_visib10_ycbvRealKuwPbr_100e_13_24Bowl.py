_base_ = "./resnest50d_AugCosyAAE_BG05_mlBCE_DoubleMask_visib10_ycbvRealKuwPbr_100e_01_02MasterChefCan.py"
OUTPUT_DIR = "output/Depth6DPose/ycbv/resnest50d_AugCosyAAE_BG05_mlBCE_DoubleMask_visib10_ycbvRealKuwPbr_100e_SO/13_24Bowl"
DATASETS = dict(TRAIN=("ycbv_024_bowl_train_real_aligned_Kuw", "ycbv_024_bowl_train_pbr"))
