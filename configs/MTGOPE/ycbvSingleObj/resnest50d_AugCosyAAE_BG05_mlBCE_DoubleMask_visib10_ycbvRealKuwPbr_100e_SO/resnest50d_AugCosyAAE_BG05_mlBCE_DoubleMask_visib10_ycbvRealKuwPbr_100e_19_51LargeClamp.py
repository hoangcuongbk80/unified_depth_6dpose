_base_ = "./resnest50d_AugCosyAAE_BG05_mlBCE_DoubleMask_visib10_ycbvRealKuwPbr_100e_01_02MasterChefCan.py"
OUTPUT_DIR = (
    "output/Depth6DPose/ycbv/resnest50d_AugCosyAAE_BG05_mlBCE_DoubleMask_visib10_ycbvRealKuwPbr_100e_SO/19_51LargeClamp"
)
DATASETS = dict(TRAIN=("ycbv_051_large_clamp_train_real_aligned_Kuw", "ycbv_051_large_clamp_train_pbr"))
