_base_ = "./resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO_01_02MasterChefCan.py"
OUTPUT_DIR = (
    "output/Depth6DPose/ycbvPbrSO/resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO/12_21BleachCleanser"
)
DATASETS = dict(TRAIN=("ycbv_021_bleach_cleanser_train_pbr",))
