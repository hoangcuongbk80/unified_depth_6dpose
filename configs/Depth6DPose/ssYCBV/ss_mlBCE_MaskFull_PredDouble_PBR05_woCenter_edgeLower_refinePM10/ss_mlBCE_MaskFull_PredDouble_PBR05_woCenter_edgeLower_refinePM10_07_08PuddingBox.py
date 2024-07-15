_base_ = "./ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_edgeLower_refinePM10_01_02MasterChefCan.py"
OUTPUT_DIR = "output/Depth6DPose/ssYCBV/ss_mlBCE_MaskFull_PredDouble_PBR05_woCenter_edgeLower_refinePM10/07_08PuddingBox"
DATASETS = dict(
    TRAIN=("ycbv_008_pudding_box_train_real_aligned_Kuw",),
    TRAIN2=("ycbv_008_pudding_box_train_pbr",),
)
MODEL = dict(
    WEIGHTS="output/Depth6DPose/ycbvPbrSO/resnest50d_AugCosyAAEGray_BG05_visib10_mlBCE_DoubleMask_ycbvPbr100e_SO/07_08PuddingBox/model_final_wo_optim-23fb01c0.pth"
)
