_base_ = "./ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_edgeLower_refinePM10_01_02MasterChefCan.py"
OUTPUT_DIR = "output/Depth6DPose/ssYCBV/ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_edgeLower_refinePM10/15_35PowerDrill"
DATASETS = dict(
    TRAIN=("ycbv_035_power_drill_train_real_aligned_Kuw",),
    TRAIN2=("ycbv_035_power_drill_train_pbr",),
)
MODEL = dict(
    WEIGHTS="output/Depth6DPose/ycbvPbrSO/resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO/15_35PowerDrill/model_final_wo_optim-0769bee7.pth"
)
