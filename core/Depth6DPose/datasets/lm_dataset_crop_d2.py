import hashlib
import logging
import os
import os.path as osp
import sys
import time
from collections import OrderedDict

import mmcv
import numpy as np
from tqdm import tqdm
from transforms3d.quaternions import mat2quat, quat2mat
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.structures import BoxMode

cur_dir = osp.dirname(osp.abspath(__file__))
PROJ_ROOT = osp.normpath(osp.join(cur_dir, "../../.."))
sys.path.insert(0, PROJ_ROOT)

import ref

from lib.pysixd import inout, misc
from lib.utils.mask_utils import binary_mask_to_rle, cocosegm2mask
from lib.utils.utils import dprint, iprint, lazy_property


logger = logging.getLogger(__name__)
DATASETS_ROOT = osp.normpath(osp.join(PROJ_ROOT, "datasets"))


class LM_CROP_Dataset(object):
    """lm crop splits."""

    def __init__(self, data_cfg):
        """
        Set with_depth and with_masks default to True,
        and decide whether to load them into dataloader/network later
        with_masks:
        """
        self.name = data_cfg["name"]
        self.data_cfg = data_cfg

        self.objs = data_cfg["objs"]  # selected objects

        self.ann_files = data_cfg["ann_files"]  # idx files with image ids
        self.image_prefixes = data_cfg["image_prefixes"]

        self.dataset_root = data_cfg["dataset_root"]  # BOP_DATASETS/lm/
        assert osp.exists(self.dataset_root), self.dataset_root
        self.models_root = data_cfg["models_root"]  # BOP_DATASETS/lm/models
        self.scale_to_meter = data_cfg["scale_to_meter"]  # 0.001

        self.with_masks = data_cfg["with_masks"]  # True (load masks but may not use it)
        self.with_depth = data_cfg["with_depth"]  # True (load depth path here, but may not use it)
        self.depth_factor = data_cfg["depth_factor"]  # 1000.0

        self.cam_type = data_cfg["cam_type"]
        self.cam = data_cfg["cam"]  #
        self.height = data_cfg["height"]  # 480
        self.width = data_cfg["width"]  # 640

        self.cache_dir = data_cfg["cache_dir"]  # .cache
        self.use_cache = data_cfg["use_cache"]  # True
        self.num_to_load = data_cfg["num_to_load"]  # -1
        self.filter_invalid = data_cfg["filter_invalid"]
        self.filter_scene = data_cfg.get("filter_scene", False)
        ##################################################
        if self.cam is None:
            assert self.cam_type in ["local", "dataset"]
            if self.cam_type == "dataset":
                self.cam = np.array([[572.4114, 0, 325.2611], [0, 573.57043, 242.04899], [0, 0, 1]])
            elif self.cam_type == "local":
                # self.cam = np.array([[539.8100, 0, 318.2700], [0, 539.8300, 239.5600], [0, 0, 1]])
                # yapf: disable
                self.cam = np.array(
                    [[518.81993115, 0.,           320.50653699],
                     [0.,           518.86581081, 243.5604188 ],
                     [0.,           0.,           1.          ]])
                # yapf: enable
                # RMS: 0.14046169348724977
                # camera matrix:
                # [[518.81993115   0.         320.50653699]
                # [  0.         518.86581081 243.5604188 ]
                # [  0.           0.           1.        ]]
                # distortion coefficients:  [ 0.04147325 -0.21469544 -0.00053707 -0.00251986  0.17406399]

        # NOTE: careful! Only the selected objects
        self.cat_ids = [cat_id for cat_id, obj_name in ref.lm_full.id2obj.items() if obj_name in self.objs]
        # map selected objs to [0, num_objs-1]
        self.cat2label = {v: i for i, v in enumerate(self.cat_ids)}  # id_map
        self.label2cat = {label: cat for cat, label in self.cat2label.items()}
        self.obj2label = OrderedDict((obj, obj_id) for obj_id, obj in enumerate(self.objs))
        ##########################################################

    def __call__(self):  # LM_CROP_Dataset
        """Load light-weight instance annotations of all images into a list of
        dicts in Detectron2 format.

        Do not load heavy data into memory in this file, since we will
        load the annotations of all images into memory.
        """
        # cache the dataset_dicts to avoid loading masks from files
        hashed_file_name = hashlib.md5(
            (
                "".join([str(fn) for fn in self.objs])
                + "dataset_dicts_{}_{}_{}_{}_{}".format(
                    self.name, self.dataset_root, self.with_masks, self.with_depth, self.cam_type
                )
            ).encode("utf-8")
        ).hexdigest()
        cache_path = osp.join(self.cache_dir, "dataset_dicts_{}_{}.pkl".format(self.name, hashed_file_name))

        if osp.exists(cache_path) and self.use_cache:
            logger.info("load cached dataset dicts from {}".format(cache_path))
            return mmcv.load(cache_path)

        t_start = time.perf_counter()

        logger.info("loading dataset dicts: {}".format(self.name))
        self.num_instances_without_valid_segmentation = 0
        self.num_instances_without_valid_box = 0
        dataset_dicts = []  #######################################################
        assert len(self.ann_files) == len(self.image_prefixes), f"{len(self.ann_files)} != {len(self.image_prefixes)}"
        unique_im_id = 0
        for ann_file, scene_root in zip(self.ann_files, self.image_prefixes):
            # linemod each scene is an object
            with open(ann_file, "r") as f_ann:
                indices = [line.strip("\r\n") for line in f_ann.readlines()]  # string ids
            gt_dict = mmcv.load(osp.join(scene_root, "scene_gt.json"))
            gt_info_dict = mmcv.load(osp.join(scene_root, "scene_gt_info.json"))  # bbox_obj, bbox_visib
            for im_id in tqdm(indices):
                int_im_id = int(im_id)
                rgb_path = osp.join(scene_root, "rgb/{:06d}.png").format(int_im_id)
                assert osp.exists(rgb_path), rgb_path

                depth_path = osp.join(scene_root, "depth/{:06d}.png".format(int_im_id))

                scene_id = int(rgb_path.split("/")[-3])
                scene_im_id = "{}/{}".format(scene_id, int_im_id)
                if self.filter_scene:
                    if scene_id not in self.cat_ids:
                        continue
                record = {
                    "dataset_name": self.name,
                    "file_name": osp.relpath(rgb_path, PROJ_ROOT),
                    "depth_file": osp.relpath(depth_path, PROJ_ROOT),
                    "height": self.height,
                    "width": self.width,
                    "image_id": unique_im_id,
                    "scene_im_id": scene_im_id,  # for evaluation
                    "cam": self.cam,
                    "depth_factor": self.depth_factor,
                    "img_type": "real",
                }
                unique_im_id += 1
                insts = []
                for anno_i, anno in enumerate(gt_dict[im_id]):
                    obj_id = anno["obj_id"]
                    if obj_id not in self.cat_ids:
                        continue
                    cur_label = self.cat2label[obj_id]  # 0-based label
                    R = np.array(anno["cam_R_m2c"], dtype="float32").reshape(3, 3)
                    t = np.array(anno["cam_t_m2c"], dtype="float32") / 1000.0
                    pose = np.hstack([R, t.reshape(3, 1)])
                    quat = mat2quat(R).astype("float32")

                    proj = (record["cam"] @ t.T).T
                    proj = proj[:2] / proj[2]

                    bbox_visib = gt_info_dict[im_id][anno_i]["bbox_visib"]
                    bbox_obj = gt_info_dict[im_id][anno_i]["bbox_obj"]
                    x1, y1, w, h = bbox_visib

                    cx, cy = proj
                    crop_x1 = round(np.clip(cx - 64, 0, self.width - 1))
                    crop_x2 = round(np.clip(cx + 64, 0, self.width - 1))
                    crop_y1 = round(np.clip(cy - 64, 0, self.height - 1))
                    crop_y2 = round(np.clip(cy + 64, 0, self.height - 1))

                    # convert to xywh
                    crop_w = crop_x2 - crop_x1
                    crop_h = crop_y2 - crop_y1
                    bbox_128 = [crop_x1, crop_y1, crop_w, crop_h]

                    if self.filter_invalid:
                        if h <= 1 or w <= 1:
                            self.num_instances_without_valid_box += 1
                            continue

                    mask_file = osp.join(scene_root, "mask/{:06d}_{:06d}.png".format(int_im_id, anno_i))
                    mask_visib_file = osp.join(scene_root, "mask_visib/{:06d}_{:06d}.png".format(int_im_id, anno_i))
                    assert osp.exists(mask_file), mask_file
                    assert osp.exists(mask_visib_file), mask_visib_file
                    # load mask visib  TODO: load both mask_visib and mask_full
                    mask_single = mmcv.imread(mask_visib_file, "unchanged")
                    mask_single = mask_single.astype("bool")
                    area = mask_single.sum()
                    if area < 3:  # filter out too small or nearly invisible instances
                        self.num_instances_without_valid_segmentation += 1
                        continue
                    mask_rle = binary_mask_to_rle(mask_single, compressed=True)
                    # load mask full
                    mask_full = mmcv.imread(mask_file, "unchanged")
                    mask_full = mask_full.astype("bool")
                    mask_full_rle = binary_mask_to_rle(mask_full, compressed=True)

                    inst = {
                        "category_id": cur_label,  # 0-based label
                        "bbox": bbox_visib,  # TODO: load both bbox_obj and bbox_visib
                        "bbox_mode": BoxMode.XYWH_ABS,
                        "bbox_crop": bbox_128,
                        "pose": pose,
                        "quat": quat,
                        "trans": t,
                        "centroid_2d": proj,  # absolute (cx, cy)
                        "segmentation": mask_rle,
                        "mask_full": mask_full_rle,
                    }
                    model_info = self.models_info[str(obj_id)]
                    inst["model_info"] = model_info
                    for key in ["bbox3d_and_center"]:
                        inst[key] = self.models[cur_label][key]
                    insts.append(inst)
                if len(insts) == 0:  # filter im without anno
                    continue
                record["annotations"] = insts
                dataset_dicts.append(record)

        if self.num_instances_without_valid_segmentation > 0:
            logger.warning(
                "Filtered out {} instances without valid segmentation. "
                "There might be issues in your dataset generation process.".format(
                    self.num_instances_without_valid_segmentation
                )
            )
        if self.num_instances_without_valid_box > 0:
            logger.warning(
                "Filtered out {} instances without valid box. "
                "There might be issues in your dataset generation process.".format(self.num_instances_without_valid_box)
            )
        ##########################################################################
        if self.num_to_load > 0:
            self.num_to_load = min(int(self.num_to_load), len(dataset_dicts))
            dataset_dicts = dataset_dicts[: self.num_to_load]
        logger.info("loaded {} dataset dicts, using {}s".format(len(dataset_dicts), time.perf_counter() - t_start))

        mmcv.mkdir_or_exist(osp.dirname(cache_path))
        mmcv.dump(dataset_dicts, cache_path, protocol=4)
        logger.info("Dumped dataset_dicts to {}".format(cache_path))
        return dataset_dicts

    @lazy_property
    def models_info(self):
        models_info_path = osp.join(self.models_root, "models_info.json")
        assert osp.exists(models_info_path), models_info_path
        models_info = mmcv.load(models_info_path)  # key is str(obj_id)
        return models_info

    @lazy_property
    def models(self):
        """Load models into a list."""
        cache_path = osp.join(self.cache_dir, "models_{}.pkl".format("_".join(self.objs)))
        if osp.exists(cache_path) and self.use_cache:
            # dprint("{}: load cached object models from {}".format(self.name, cache_path))
            return mmcv.load(cache_path)

        models = []
        for obj_name in self.objs:
            model = inout.load_ply(
                osp.join(
                    self.models_root,
                    f"obj_{ref.lm_full.obj2id[obj_name]:06d}.ply",
                ),
                vertex_scale=self.scale_to_meter,
            )
            # NOTE: the bbox3d_and_center is not obtained from centered vertices
            # for BOP models, not a big problem since they had been centered
            model["bbox3d_and_center"] = misc.get_bbox3d_and_center(model["pts"])

            models.append(model)
        logger.info("cache models to {}".format(cache_path))
        mmcv.mkdir_or_exist(osp.dirname(cache_path))
        mmcv.dump(models, cache_path, protocol=4)
        return models

    def __len__(self):
        # return len(self.images)
        return self.num_to_load

    def image_aspect_ratio(self):
        return self.width / self.height  # 4/3


########### register datasets ############################################################


def get_lm_metadata(obj_names, ref_key):
    """task specific metadata."""

    data_ref = ref.__dict__[ref_key]

    cur_sym_infos = {}  # label based key
    loaded_models_info = data_ref.get_models_info()

    for i, obj_name in enumerate(obj_names):
        obj_id = data_ref.obj2id[obj_name]
        model_info = loaded_models_info[str(obj_id)]
        if "symmetries_discrete" in model_info or "symmetries_continuous" in model_info:
            sym_transforms = misc.get_symmetry_transformations(model_info, max_sym_disc_step=0.01)
            sym_info = np.array([sym["R"] for sym in sym_transforms], dtype=np.float32)
        else:
            sym_info = None
        cur_sym_infos[i] = sym_info

    meta = {"thing_classes": obj_names, "sym_infos": cur_sym_infos}
    return meta


LM_CROP_11_OBJECTS = [
    "ape",
    "benchvise",
    "camera",
    "can",
    "cat",
    "driller",
    "duck",
    "holepuncher",
    "iron",
    "lamp",
    "phone",
]  # no bowl, cup, eggbox, glue
################################################################################

SPLITS_LM_CROP = dict(
    lm_crop_11_train=dict(
        name="lm_crop_11_train",
        dataset_root=osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/"),
        models_root=osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/models"),
        objs=LM_CROP_11_OBJECTS,  # selected objects
        ann_files=[
            osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/image_set_lm_crop/lm_crop_{}_{}.txt".format("train", _obj))
            for _obj in LM_CROP_11_OBJECTS
        ],
        image_prefixes=[
            osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/test/{:06d}".format(ref.lm_full.obj2id[_obj]))
            for _obj in LM_CROP_11_OBJECTS
        ],
        scale_to_meter=0.001,
        with_masks=True,  # (load masks but may not use it)
        with_depth=True,  # (load depth path here, but may not use it)
        depth_factor=1000.0,
        cam_type="dataset",
        cam=ref.lm_full.camera_matrix,
        height=480,
        width=640,
        cache_dir=osp.join(PROJ_ROOT, ".cache"),
        use_cache=True,
        num_to_load=-1,
        filter_scene=True,
        filter_invalid=False,
        ref_key="lm_full",
    ),
    lm_crop_11_test=dict(
        name="lm_crop_11_test",
        dataset_root=osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/"),
        models_root=osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/models"),
        objs=LM_CROP_11_OBJECTS,
        ann_files=[
            osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/image_set_lm_crop/lm_crop_{}_{}.txt".format("test", _obj))
            for _obj in LM_CROP_11_OBJECTS
        ],
        # NOTE: scene root
        image_prefixes=[
            osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/test/{:06d}").format(ref.lm_full.obj2id[_obj])
            for _obj in LM_CROP_11_OBJECTS
        ],
        scale_to_meter=0.001,
        with_masks=True,  # (load masks but may not use it)
        with_depth=True,  # (load depth path here, but may not use it)
        depth_factor=1000.0,
        cam_type="dataset",
        cam=ref.lm_full.camera_matrix,
        height=480,
        width=640,
        cache_dir=osp.join(PROJ_ROOT, ".cache"),
        use_cache=True,
        num_to_load=-1,
        filter_scene=True,
        filter_invalid=False,
        ref_key="lm_full",
    ),
)

# single obj splits
for obj in ref.lm_full.objects:
    for split in ["train", "test"]:
        name = "lm_crop_{}_{}".format(obj, split)
        ann_files = [osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/image_set_lm_crop/lm_crop_{}_{}.txt".format(split, obj))]
        if split in ["train"]:
            filter_invalid = True
        elif split in ["test"]:
            filter_invalid = False
        else:
            raise ValueError("{}".format(split))
        if name not in SPLITS_LM_CROP:
            SPLITS_LM_CROP[name] = dict(
                name=name,
                dataset_root=osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/"),
                models_root=osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/models"),
                objs=[obj],  # only this obj
                ann_files=ann_files,
                image_prefixes=[osp.join(DATASETS_ROOT, "BOP_DATASETS/lm/test/{:06d}").format(ref.lm_full.obj2id[obj])],
                scale_to_meter=0.001,
                with_masks=True,  # (load masks but may not use it)
                with_depth=True,  # (load depth path here, but may not use it)
                depth_factor=1000.0,
                cam_type="dataset",
                cam=ref.lm_full.camera_matrix,
                height=480,
                width=640,
                cache_dir=osp.join(PROJ_ROOT, ".cache"),
                use_cache=True,
                num_to_load=-1,
                filter_invalid=False,
                filter_scene=True,
                ref_key="lm_full",
            )


def register_with_name_cfg(name, data_cfg=None):
    """Assume pre-defined datasets live in `./datasets`.

    Args:
        name: datasnet_name,
        data_cfg: if name is in existing SPLITS, use pre-defined data_cfg
            otherwise requires data_cfg
            data_cfg can be set in cfg.DATA_CFG.name
    """
    dprint("register dataset: {}".format(name))
    if name in SPLITS_LM_CROP:
        used_cfg = SPLITS_LM_CROP[name]
    else:
        assert data_cfg is not None, f"dataset name {name} is not registered"
        used_cfg = data_cfg
    DatasetCatalog.register(name, LM_CROP_Dataset(used_cfg))
    # something like eval_types
    MetadataCatalog.get(name).set(
        ref_key=used_cfg["ref_key"],
        objs=used_cfg["objs"],
        eval_error_types=["ad", "rete", "proj"],
        evaluator_type="bop",
        **get_lm_metadata(obj_names=used_cfg["objs"], ref_key=used_cfg["ref_key"]),
    )


def get_available_datasets():
    return list(SPLITS_LM_CROP.keys())


#### tests ###############################################
def test_vis():
    # python -m this_module lmo_test
    dset_name = sys.argv[1]
    assert dset_name in DatasetCatalog.list()

    meta = MetadataCatalog.get(dset_name)
    dprint("MetadataCatalog: ", meta)
    objs = meta.objs

    t_start = time.perf_counter()
    dicts = DatasetCatalog.get(dset_name)
    logger.info("Done loading {} samples with {:.3f}s.".format(len(dicts), time.perf_counter() - t_start))

    dirname = "output/{}-data-vis".format(dset_name)
    os.makedirs(dirname, exist_ok=True)
    for d in dicts:
        img = read_image_mmcv(d["file_name"], format="BGR")
        depth = mmcv.imread(d["depth_file"], "unchanged") / 1000.0

        imH, imW = img.shape[:2]
        annos = d["annotations"]
        masks = [cocosegm2mask(anno["segmentation"], imH, imW) for anno in annos]
        bboxes = [anno["bbox"] for anno in annos]
        bbox_modes = [anno["bbox_mode"] for anno in annos]
        bboxes_xyxy = np.array(
            [BoxMode.convert(box, box_mode, BoxMode.XYXY_ABS) for box, box_mode in zip(bboxes, bbox_modes)]
        )
        kpts_3d_list = [anno["bbox3d_and_center"] for anno in annos]
        quats = [anno["quat"] for anno in annos]
        centers_2d = [anno["centroid_2d"] for anno in annos]
        bboxes_128 = []
        for center_2d in centers_2d:
            cx, cy = center_2d
            bboxes_128.append([cx - 64, cy - 64, cx + 64, cy + 64])
        bboxes_128 = np.array(bboxes_128)
        bboxes_128[:, 0] = np.clip(bboxes_128[:, 0], 0, imW - 1)
        bboxes_128[:, 2] = np.clip(bboxes_128[:, 2], 0, imW - 1)
        bboxes_128[:, 1] = np.clip(bboxes_128[:, 1], 0, imH - 1)
        bboxes_128[:, 3] = np.clip(bboxes_128[:, 3], 0, imH - 1)

        transes = [anno["trans"] for anno in annos]
        Rs = [quat2mat(quat) for quat in quats]
        # 0-based label
        cat_ids = [anno["category_id"] for anno in annos]
        K = d["cam"]
        kpts_2d = [misc.project_pts(kpt3d, K, R, t) for kpt3d, R, t in zip(kpts_3d_list, Rs, transes)]
        # visualizer = Visualizer(img[:, :, [2,1,0]], metadata=meta)
        # vis = visualizer.draw_dataset_dict(d)  # TODO: add pose visualization and depth visualization
        # # fpath = osp.join(dirname, osp.basename(d["file_name"]))
        # # vis.save(fpath)
        # img_vis = vis.get_image()[:, :, [2,1,0]]
        # # TODO: visualize pose and keypoints
        labels = [objs[cat_id] for cat_id in cat_ids]
        # img_vis = vis_image_bboxes_cv2(img, bboxes=bboxes_xyxy, labels=labels)
        img_vis = vis_image_mask_bbox_cv2(img, masks, bboxes=bboxes_xyxy, labels=labels)
        img_vis_kpts2d = img.copy()
        for anno_i in range(len(annos)):
            img_vis_kpts2d = misc.draw_projected_box3d(img_vis_kpts2d, kpts_2d[anno_i])
        img_vis_bbox_128 = vis_image_mask_bbox_cv2(img, masks, bboxes=bboxes_128, labels=labels)

        grid_show(
            [img_vis_bbox_128[:, :, ::-1], depth],
            ["img_vis_bbox_128", "depth"],
            row=1,
            col=2,
        )


if __name__ == "__main__":
    """Test the  dataset loader.

    Usage:
        python -m core.datasets.lm_dataset_d2 dataset_name
    """
    from lib.vis_utils.image import grid_show
    from lib.utils.setup_logger import setup_my_logger
    from detectron2.utils.visualizer import Visualizer
    import detectron2.data.datasets  # noqa # add pre-defined metadata
    from lib.pysixd import misc
    from core.utils.data_utils import read_image_mmcv
    from lib.vis_utils.image import vis_image_mask_bbox_cv2
    from lib.utils.mask_utils import cocosegm2mask
    from lib.utils.bbox_utils import xywh_to_xyxy

    print("sys.argv:", sys.argv)
    logger = setup_my_logger(name="core")
    register_with_name_cfg(sys.argv[1])
    print("dataset catalog: ", DatasetCatalog.list())
    test_vis()
