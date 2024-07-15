_base_ = "./ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_woDepth_edgeLower_refinePM10_01_02MasterChefCan.py"
OUTPUT_DIR = (
    "output/Depth6DPose/ssYCBV/ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_woDepth_edgeLower_refinePM10/21_61FoamBrick"
)
DATASETS = dict(
    TRAIN=("ycbv_061_foam_brick_train_real_aligned_Kuw",),
    TRAIN2=("ycbv_061_foam_brick_train_pbr",),
)
MODEL = dict(
    WEIGHTS="output/Depth6DPose/ycbvPbrSO/resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO/21_61FoamBrick/model_final_wo_optim-375a4cba.pth"
)
