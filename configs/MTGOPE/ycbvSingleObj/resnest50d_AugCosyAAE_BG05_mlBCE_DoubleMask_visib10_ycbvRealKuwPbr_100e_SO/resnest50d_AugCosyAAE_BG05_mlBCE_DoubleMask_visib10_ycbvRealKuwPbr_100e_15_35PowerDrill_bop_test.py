_base_ = "./resnest50d_AugCosyAAE_BG05_mlBCE_DoubleMask_visib10_ycbvRealKuwPbr_100e_01_02MasterChefCan_bop_test.py"
OUTPUT_DIR = (
    "output/Depth6DPose/ycbv/resnest50d_AugCosyAAE_BG05_mlBCE_DoubleMask_visib10_ycbvRealKuwPbr_100e_SO/15_35PowerDrill"
)
DATASETS = dict(TRAIN=("ycbv_035_power_drill_train_real_aligned_Kuw", "ycbv_035_power_drill_train_pbr"))
