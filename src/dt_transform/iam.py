"""Transform IAM dataset"""

from multiprocessing import Pool
from functools import partial
import h5py
import os


def dataset(env, preproc, encode):
    """Load and save hdf5 file of the ground truth and images (preprocessed)"""

    def transform(group, target):
        with h5py.File(env.source, "a") as hf:
            dt, gt = build_data(env, target, gt_dict, preproc, encode)
            hf.create_dataset(f"{group}/dt", data=dt, compression="gzip", compression_opts=9)
            hf.create_dataset(f"{group}/gt", data=gt, compression="gzip", compression_opts=9)
            print(f"[OK] {group} partition.")
            del dt, gt

    gt = os.path.join(env.raw_source, "ascii")
    ground_truth = open(os.path.join(gt, "lines.txt")).read().splitlines()
    gt_dict = dict()

    for line in ground_truth:
        if (not line or line[0] == "#"):
            continue

        splited = line.strip().split(" ")
        assert len(splited) >= 9

        name = splited[0].strip()
        text = splited[len(splited) - 1].replace("|", " ").strip()
        gt_dict[name] = text

    transform(group="test", target="testset.txt")
    transform(group="valid", target="validationset1.txt")
    transform(group="train", target="trainset.txt")


def build_data(env, partition, gt_dict, preproc, encode):
    """Preprocess images with pool function"""

    pt_path = os.path.join(env.raw_source, "largeWriterIndependentTextLineRecognitionTask")
    lines = open(os.path.join(pt_path, partition)).read().splitlines()
    data_path = os.path.join(env.raw_source, "lines")
    dt, gt = [], []

    for line in lines:
        text_line = gt_dict[line].strip()

        if len(text_line) > 0:
            split = line.split("-")
            path = os.path.join(split[0], f"{split[0]}-{split[1]}", f"{split[0]}-{split[1]}-{split[2]}.png")
            path = os.path.join(data_path, path)

            dt.append(path)
            gt.append(text_line)

    pool = Pool()
    dt = pool.map(partial(preproc, img_size=env.input_size, read_first=True), dt)
    gt = pool.map(partial(encode, charset=env.charset, mtl=env.max_text_length), gt)
    pool.close()
    pool.join()

    return dt, gt
