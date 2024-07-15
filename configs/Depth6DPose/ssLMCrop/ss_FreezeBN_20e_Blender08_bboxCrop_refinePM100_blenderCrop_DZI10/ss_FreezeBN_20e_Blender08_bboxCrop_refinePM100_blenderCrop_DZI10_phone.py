_base_ = ["ss_FreezeBN_20e_Blender08_bboxCrop_refinePM100_blenderCrop_DZI10_ape.py"]

# refiner_cfg_path = "configs/_base_/Depth6DPose_refiner_base.py"

OUTPUT_DIR = "output/Depth6DPose/ssLMCrop/FreezeBN_20e_Blender08_bboxCrop_refinePM100_blenderCrop_DZI10/phone"

DATASETS = dict(
    TRAIN=("lm_crop_phone_train",),  # real data
    TRAIN2=("lm_blender_phone_train",),  # synthetic data
    TEST=("lm_crop_phone_test",),
)


MODEL = dict(
    # synthetically trained model
    WEIGHTS="output/Depth6DPose/lm_crop_blender/resnest50d_a6_AugCosyAAEGray_BG05_mlBCE_bboxCrop_DZI10_lm_blender_100e/phone/model_final_wo_optim-4172540b.pth"
)
