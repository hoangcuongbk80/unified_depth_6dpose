_base_ = "./resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO_bop_test_01_02MasterChefCan.py"
OUTPUT_DIR = (
    "output/Depth6DPose/ycbvPbrSO/resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO/03_04SugarBox"
)
DATASETS = dict(TRAIN=("ycbv_004_sugar_box_train_pbr",))
