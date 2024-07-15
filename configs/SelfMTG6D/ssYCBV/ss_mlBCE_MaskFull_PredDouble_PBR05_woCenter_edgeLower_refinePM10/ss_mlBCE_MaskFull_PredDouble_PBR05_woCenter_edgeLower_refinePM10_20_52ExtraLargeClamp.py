_base_ = "./ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_edgeLower_refinePM10_01_02MasterChefCan.py"
OUTPUT_DIR = (
    "output/Depth6DPose/ssYCBV/ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_edgeLower_refinePM10/20_52ExtraLargeClamp"
)
DATASETS = dict(
    TRAIN=("ycbv_052_extra_large_clamp_train_real_aligned_Kuw",),
    TRAIN2=("ycbv_052_extra_large_clamp_train_pbr",),
)
MODEL = dict(
    WEIGHTS="output/Depth6DPose/ycbvPbrSO/resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO/20_52ExtraLargeClamp/model_final_wo_optim-82f2dafa.pth"
)
