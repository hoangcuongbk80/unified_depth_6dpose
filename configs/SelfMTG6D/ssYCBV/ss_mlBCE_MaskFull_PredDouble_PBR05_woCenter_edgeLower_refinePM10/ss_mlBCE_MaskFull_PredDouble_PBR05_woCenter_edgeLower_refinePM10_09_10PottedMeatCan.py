_base_ = "./ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_edgeLower_refinePM10_01_02MasterChefCan.py"
OUTPUT_DIR = (
    "output/Depth6DPose/ssYCBV/ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_edgeLower_refinePM10/09_10PottedMeatCan"
)
DATASETS = dict(
    TRAIN=("ycbv_010_potted_meat_can_train_real_aligned_Kuw",),
    TRAIN2=("ycbv_010_potted_meat_can_train_pbr",),
)
MODEL = dict(
    WEIGHTS="output/Depth6DPose/ycbvPbrSO/resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO/09_10PottedMeatCan/model_final_wo_optim-cc1232e2.pth"
)
