
### Installl

* Ubuntu 16.04/18.04, CUDA 10.2, python >= 3.6, PyTorch >= 1.7.1, torchvision
* `sh scripts/install_deps.sh`

### Datasets

Download the YCB-Video and  datasets Occluded-LINEMOD from the
[BOP website](https://bop.felk.cvut.cz/datasets/).

The structure of `datasets` folder should look like below:
```
# recommend using soft links (ln -sf)
datasets/
├── BOP_DATASETS   # https://bop.felk.cvut.cz/datasets/
    ├──ycbv
```

### Training

```
core/Depth6DPose/train.sh <config_path> <gpu_ids> (other args)
```

### Testing

```
core/Depth6DPose/test.sh <config_path> <gpu_ids> (other args)
```