_base_ = "./resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO_bop_test_01_02MasterChefCan.py"
OUTPUT_DIR = (
    "output/Depth6DPose/ycbvPbrSO/resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO/08_09GelatinBox"
)
DATASETS = dict(TRAIN=("ycbv_009_gelatin_box_train_pbr",))
