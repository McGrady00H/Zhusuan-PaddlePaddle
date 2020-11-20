import os
import math
import gzip
import progressbar
import six
import numpy as np
from six.moves import urllib, range
from six.moves import cPickle as pickle
from PIL import Image
from matplotlib import pyplot as plt

from paddle.io import Dataset

pbar = None
examples_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(examples_dir, "data")
data_path = os.path.join(data_dir, "mnist.pkl.gz")

def show_progress(block_num, block_size, total_size):
    global pbar
    if pbar is None:
        if total_size > 0:
            prefixes = ('', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi', 'Yi')
            power = min(int(math.log(total_size, 2) / 10), len(prefixes) - 1)
            scaled = float(total_size) / (2 ** (10 * power))
            total_size_str = '{:.1f} {}B'.format(scaled, prefixes[power])
            try:
                marker = '█'
            except UnicodeEncodeError:
                marker = '*'
            widgets = [
                progressbar.Percentage(),
                ' ', progressbar.DataSize(),
                ' / ', total_size_str,
                ' ', progressbar.Bar(marker=marker),
                ' ', progressbar.ETA(),
                ' ', progressbar.AdaptiveTransferSpeed(),
            ]
            pbar = progressbar.ProgressBar(widgets=widgets,
                                           max_value=total_size)
        else:
            widgets = [
                progressbar.DataSize(),
                ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
                ' ', progressbar.Timer(),
                ' ', progressbar.AdaptiveTransferSpeed(),
            ]
            pbar = progressbar.ProgressBar(widgets=widgets,
                                           max_value=progressbar.UnknownLength)

    downloaded = block_num * block_size
    if downloaded < total_size:
        pbar.update(downloaded)
    else:
        pbar.finish()
        pbar = None

def download_dataset(url, path):
    print('Downloading data from %s' % url)
    #urllib.request.urlretrieve(url, path, show_progress)
    urllib.request.urlretrieve(url, path)

def to_one_hot(x, depth):
    """
    Get one-hot representation of a 1-D numpy array of integers.

    :param x: 1-D Numpy array of type int.
    :param depth: A int.

    :return: 2-D Numpy array of type int.
    """
    ret = np.zeros((x.shape[0], depth))
    ret[np.arange(x.shape[0]), x] = 1
    return ret

def load_mnist_realval(path=data_path, one_hot=True, dequantify=False):
    """
    Loads the real valued MNIST dataset.

    :param path: Path to the dataset file.
    :param one_hot: Whether to use one-hot representation for the labels.
    :param dequantify:  Whether to add uniform noise to dequantify the data
        following (Uria, 2013).

    :return: The MNIST dataset.
    """
    if not os.path.isfile(path):
        data_dir = os.path.dirname(path)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(data_dir)
        download_dataset('http://www.iro.umontreal.ca/~lisa/deep/data/mnist'
                         '/mnist.pkl.gz', path)

    f = gzip.open(path, 'rb')
    if six.PY2:
        train_set, valid_set, test_set = pickle.load(f)
    else:
        train_set, valid_set, test_set = pickle.load(f, encoding='latin1')
    f.close()
    x_train, t_train = train_set[0], train_set[1]
    x_valid, t_valid = valid_set[0], valid_set[1]
    x_test, t_test = test_set[0], test_set[1]
    # x_train, t_train = train_set[0][:64*500], train_set[1][:64*500]
    # x_valid, t_valid = valid_set[0][:64*50], valid_set[1][:64*50]
    # x_test, t_test = test_set[0][:64*10], test_set[1][:64*10]
    if dequantify:
        x_train += np.random.uniform(0, 1. / 256,
                                     size=x_train.shape).astype('float32')
        x_valid += np.random.uniform(0, 1. / 256,
                                     size=x_valid.shape).astype('float32')
        x_test += np.random.uniform(0, 1. / 256,
                                    size=x_test.shape).astype('float32')
    n_y = t_train.max() + 1
    t_transform = (lambda x: to_one_hot(x, n_y)) if one_hot else (lambda x: x)
    return x_train, t_transform(t_train), x_valid, t_transform(t_valid), \
        x_test, t_transform(t_test)


def save_img(data, name):
    """
    Visualize data and save to target files
    Args:
        data: nparray of size (num, size, size)
        name: ouput file name
        size: image size
        num: number of images
    """

    size = int(data.shape[1]**.5)
    num = data.shape[0]
    col = int(num / 8)
    row = 8

    imgs = Image.new('L', (size*col, size*row))
    for i in range(num):
        j = i/8
        img_data = data[i]
        img_data  = np.resize(img_data, (size, size))
        img_data = img_data * 255
        img_data = img_data.astype(np.uint8)
        im = Image.fromarray(img_data, 'L')
        imgs.paste(im, (int(j) * size , (i % 8) * size))
    imgs.save(name)


class MNISTDataset(Dataset):
    def __init__(self, mode='train'):
        super(MNISTDataset, self).__init__()
        # Load MNIST
        data_path = os.path.join(data_dir, "mnist.pkl.gz")
        x_train, t_train, x_valid, t_valid, x_test, t_test = load_mnist_realval(data_path)
        if mode == 'train':
            self.data = x_train
            self.labels = t_train
        elif mode == 'test':
            self.data = x_test
            self.labels = t_test
        else:
            self.data = x_valid
            self.labels = t_valid

    def __getitem__(self, index):
        return self.data[index], self.labels[index]

    def __len__(self):
        return len(self.data)
