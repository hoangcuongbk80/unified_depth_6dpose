_base_ = "./ss_v1_dibr_mlBCE_FreezeBN_woCenter_refinePM10_ape.py"
OUTPUT_DIR = "output/Depth6DPose/ssLM/ss_v1_dibr_mlBCE_FreezeBN_woCenter_refinePM10/glue"
DATASETS = dict(
    TRAIN=("lm_real_glue_train",), TRAIN2=("lm_pbr_glue_train",), TRAIN2_RATIO=0.0, TEST=("lm_real_glue_test",)
)
MODEL = dict(
    WEIGHTS="output/Depth6DPose/lm_pbr/resnest50d_a6_AugCosyAAEGray_BG05_mlBCE_lm_pbr_100e/glue_Rsym/model_final_wo_optim-324d8f16.pth"
)
