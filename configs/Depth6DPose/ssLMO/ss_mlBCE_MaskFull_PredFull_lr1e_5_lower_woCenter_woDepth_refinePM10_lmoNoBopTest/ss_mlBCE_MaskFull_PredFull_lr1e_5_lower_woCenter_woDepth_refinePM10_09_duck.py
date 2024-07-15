_base_ = ["ss_mlBCE_MaskFull_PredFull_lr1e_5_lower_woCenter_woDepth_refinePM10_01_ape.py"]

OUTPUT_DIR = (
    "output/Depth6DPose/ssLMO/ss_mlBCE_MaskFull_PredFull_lr1e_5_lower_woCenter_woDepth_refinePM10_lmoNoBopTest/duck"
)

DATASETS = dict(TRAIN=("lmo_NoBopTest_duck_train",), TRAIN2=("lmo_pbr_duck_train",))  # real data  # synthetic data

MODEL = dict(
    # synthetically trained model
    WEIGHTS="output/Depth6DPose/lmoPbrSO/resnest50d_online_AugCosyAAEGray_mlBCE_DoubleMask_lmo_pbr_100e/duck/model_final_wo_optim-3cc3dbe6.pth"
)
