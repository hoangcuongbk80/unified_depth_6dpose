_base_ = "./resnest50d_AugCosyAAE_BG05_mlBCE_DoubleMask_visib10_ycbvRealKuwPbr_100e_01_02MasterChefCan.py"
OUTPUT_DIR = (
    "output/Depth6DPose/ycbv/resnest50d_AugCosyAAE_BG05_mlBCE_DoubleMask_visib10_ycbvRealKuwPbr_100e_SO/11_19PitcherBase"
)
DATASETS = dict(TRAIN=("ycbv_019_pitcher_base_train_real_aligned_Kuw", "ycbv_019_pitcher_base_train_pbr"))
