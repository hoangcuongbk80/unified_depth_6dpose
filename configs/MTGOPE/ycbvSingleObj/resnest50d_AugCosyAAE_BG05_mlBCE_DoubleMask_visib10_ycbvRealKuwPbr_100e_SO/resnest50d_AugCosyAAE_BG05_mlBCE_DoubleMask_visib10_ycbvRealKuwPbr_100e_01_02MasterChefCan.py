_base_ = ["../../../_base_/Depth6DPose_base.py"]

OUTPUT_DIR = (
    "output/Depth6DPose/ycbv/resnest50d_AugCosyAAE_BG05_mlBCE_DoubleMask_visib10_ycbvRealKuwPbr_100e_SO/01_02MasterChefCan"
)
INPUT = dict(
    DZI_PAD_SCALE=1.5,
    TRUNCATE_FG=False,
    CHANGE_BG_PROB=0.5,
    COLOR_AUG_PROB=0.8,
    COLOR_AUG_TYPE="code",
    COLOR_AUG_CODE=(
        "Sequential(["
        # Sometimes(0.5, PerspectiveTransform(0.05)),
        # Sometimes(0.5, CropAndPad(percent=(-0.05, 0.1))),
        # Sometimes(0.5, Affine(scale=(1.0, 1.2))),
        "Sometimes(0.5, CoarseDropout( p=0.2, size_percent=0.05) ),"
        "Sometimes(0.4, GaussianBlur((0., 3.))),"
        "Sometimes(0.3, pillike.EnhanceSharpness(factor=(0., 50.))),"
        "Sometimes(0.3, pillike.EnhanceContrast(factor=(0.2, 50.))),"
        "Sometimes(0.5, pillike.EnhanceBrightness(factor=(0.1, 6.))),"
        "Sometimes(0.3, pillike.EnhanceColor(factor=(0., 20.))),"
        "Sometimes(0.5, Add((-25, 25), per_channel=0.3)),"
        "Sometimes(0.3, Invert(0.2, per_channel=True)),"
        "Sometimes(0.5, Multiply((0.6, 1.4), per_channel=0.5)),"
        "Sometimes(0.5, Multiply((0.6, 1.4))),"
        "Sometimes(0.1, AdditiveGaussianNoise(scale=10, per_channel=True)),"
        "Sometimes(0.5, iaa.contrast.LinearContrast((0.5, 2.2), per_channel=0.3)),"
        "Sometimes(0.5, Grayscale(alpha=(0.0, 1.0))),"  # maybe remove for det
        "], random_order=True)"
        # cosy+aae
    ),
)

SOLVER = dict(
    IMS_PER_BATCH=24,
    TOTAL_EPOCHS=100,
    LR_SCHEDULER_NAME="flat_and_anneal",
    ANNEAL_METHOD="cosine",  # "cosine"
    ANNEAL_POINT=0.72,
    # REL_STEPS=(0.3125, 0.625, 0.9375),
    OPTIMIZER_CFG=dict(_delete_=True, type="Ranger", lr=1e-4, weight_decay=0),
    WEIGHT_DECAY=0.0,
    WARMUP_FACTOR=0.001,
    WARMUP_ITERS=1000,
    CHECKPOINT_PERIOD=5,
)

DATASETS = dict(
    TRAIN=(
        "ycbv_002_master_chef_can_train_real_aligned_Kuw",
        "ycbv_002_master_chef_can_train_pbr",
    ),
    TEST=("ycbv_test",),
    # AP	AP50	AP75	AR	inf.time
    # 71.81 	92.32 	82.24 	81.00 	24.7ms
    DET_FILES_TEST=(
        "datasets/BOP_DATASETS/ycbv/test/test_bboxes/yolov4x_640_test672_augCosyAAEGray_ranger_ycbv_pbr_ycbv_test_16e.json",
    ),
    # # AP     AP50   AR   inf.time  (fcos_V57)
    # # 79.581 96.949 84.2 56.572ms
    # DET_FILES_TEST=(
    #     "datasets/BOP_DATASETS/ycbv/test/test_bboxes/fcos_V57eSE_MSx1333_ColorAugAAEWeaker_8e_ycbv_real_pbr_8e_test_keyframe.json",
    # ),
    DET_THR=0.3,
    SYM_OBJS=["024_bowl", "036_wood_block", "051_large_clamp", "052_extra_large_clamp", "061_foam_brick"],  # ycbv
)

DATALOADER = dict(
    # Number of data loading threads
    NUM_WORKERS=4,
    FILTER_VISIB_THR=0.1,
    FILTER_EMPTY_DETS=True,  # filter images with empty detections
)

MODEL = dict(
    LOAD_DETS_TEST=True,
    PIXEL_MEAN=[0.0, 0.0, 0.0],
    PIXEL_STD=[255.0, 255.0, 255.0],
    POSE_NET=dict(
        NAME="Depth6DPose_double_mask",
        XYZ_ONLINE=True,
        NUM_CLASSES=21,  # not used for class-agnostic
        BACKBONE=dict(
            FREEZE=False,
            PRETRAINED="timm",
            INIT_CFG=dict(
                type="timm/resnest50d",
                pretrained=True,
                in_chans=3,
                features_only=True,
                out_indices=(4,),
            ),
        ),
        ## geo head: Mask, XYZ, Region
        GEO_HEAD=dict(
            FREEZE=False,
            INIT_CFG=dict(
                type="TopDownDoubleMaskXyzRegionHead",
                in_dim=2048,  # this is num out channels of backbone conv feature
            ),
            NUM_REGIONS=64,
        ),
        PNP_NET=dict(
            INIT_CFG=dict(norm="GN", act="gelu"),
            REGION_ATTENTION=True,
            WITH_2D_COORD=True,
            ROT_TYPE="allo_rot6d",
            TRANS_TYPE="centroid_z",
        ),
        LOSS_CFG=dict(
            # xyz loss ----------------------------
            XYZ_LOSS_TYPE="L1",  # L1 | CE_coor
            XYZ_LOSS_MASK_GT="visib",  # trunc | visib | obj
            XYZ_LW=1.0,
            # mask loss ---------------------------
            MASK_LOSS_TYPE="BCE",  # L1 | BCE | CE
            MASK_LOSS_GT="trunc",  # trunc | visib | gt
            MASK_LW=1.0,
            # full mask loss ---------------------------
            FULL_MASK_LOSS_TYPE="BCE",  # L1 | BCE | CE
            FULL_MASK_LW=1.0,
            # region loss -------------------------
            REGION_LOSS_TYPE="CE",  # CE
            REGION_LOSS_MASK_GT="visib",  # trunc | visib | obj
            REGION_LW=1.0,
            # pm loss --------------
            PM_LOSS_SYM=True,  # NOTE: sym loss
            PM_R_ONLY=True,  # only do R loss in PM
            PM_LW=1.0,
            # centroid loss -------
            CENTROID_LOSS_TYPE="L1",
            CENTROID_LW=1.0,
            # z loss -----------
            Z_LOSS_TYPE="L1",
            Z_LW=1.0,
        ),
    ),
)

VAL = dict(
    DATASET_NAME="ycbvposecnn",
    SPLIT_TYPE="",
    SCRIPT_PATH="lib/pysixd/scripts/eval_pose_results_more.py",
    TARGETS_FILENAME="ycbv_test_targets_keyframe.json",  # 'lm_test_targets_bb8.json'
    ERROR_TYPES="AUCadd,AUCadi,AUCad,ABSadd,ABSadi,ABSad,reS,teS,reteS,ad",
    USE_BOP=True,  # whether to use bop toolkit
)

TEST = dict(EVAL_PERIOD=0, VIS=False, TEST_BBOX_TYPE="est")  # gt | est
