# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Script for generating a COG dataset"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import errno
import functools

import timeit
import cv2
from PIL import Image
import gzip
import itertools
import json
import multiprocessing
import os
import re
import random
import shutil
import traceback
from collections import defaultdict
import numpy as np
import tensorflow.compat.v1 as tf

from cognitive import stim_generator as sg
from cognitive import task_generator as tg
import cognitive.task_bank as task_bank
import cognitive.constants as const
import cognitive.info_generator as ig
from cognitive.arguments import get_args

try:
    range_fn = xrange  # py 2
except NameError:
    range_fn = range  # py 3


def log_exceptions(func):
    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseException as e:
            print('Exception in ' + func.__name__)
            traceback.print_exc()
            raise e

    return wrapped_func


class FileWriter(object):
    """Writes per_file examples in a file. Then, picks a new file."""

    def __init__(self, base_name, per_file=100, start_index=0, compress=True):
        self.per_file = per_file
        self.base_name = base_name
        self.compress = compress
        self.cur_file_index = start_index - 1
        self.cur_file = None
        self.written = 0
        self.file_names = []

        self._new_file()

    def _file_name(self):
        return '%s_%d.json' % (self.base_name, self.cur_file_index)

    def _new_file(self):
        if self.cur_file:
            self.close()

        self.written = 0
        self.cur_file_index += 1
        # 'b' is needed because we want to seek from the end. Text files
        # don't allow seeking from the end (because width of one char is
        # not fixed)
        self.cur_file = open(self._file_name(), 'wb')
        self.file_names.append(self._file_name())

    def write(self, data):
        if self.written >= self.per_file:
            self._new_file()
        self.cur_file.write(data)
        self.cur_file.write(b'\n')
        self.written += 1

    def close(self):
        self.cur_file.seek(-1, os.SEEK_END)
        # Remove last new line
        self.cur_file.truncate()
        self.cur_file.close()

        if self.compress:
            # Compress the file and delete the original. We can write to compressed
            # file immediately because truncate() does not work on compressed files.
            with open(self._file_name(), 'rb') as f_in, \
                    gzip.open(self._file_name() + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

            os.remove(self._file_name())


def add_fixation_cue(canvas, cue_size=0.05):
    """

    :param canvas: numpy array of shape: (img_size, img_size, 3)
    :param cue_size: size of the fixation cue
    :return:
    """
    img_size = canvas.shape[0]
    radius = int(cue_size * img_size)
    center = (canvas.shape[0] // 2, canvas.shape[1] // 2)
    thickness = int(0.02 * img_size)
    cv2.line(canvas, (center[0] - radius, center[1]),
             (center[0] + radius, center[1]), (255, 255, 255), thickness)
    cv2.line(canvas, (center[0], center[1] - radius),
             (center[0], center[1] + radius), (255, 255, 255), thickness)


def write_task_instance(fname, task_info, img_size, fixation_cue=True):
    if not os.path.exists(fname):
        os.makedirs(fname)
    objset = task_info.frame_info.objset
    for i, (epoch, frame) in enumerate(zip(sg.render(objset, img_size), task_info.frame_info)):
        if fixation_cue:
            if not any('ending' in description for description in frame.description):
                add_fixation_cue(epoch)
        img = Image.fromarray(epoch, 'RGB')
        filename = os.path.join(fname, f'epoch{i}.png')
        img.save(filename)

    examples, compo_example = task_info.get_examples()
    for i, task_example in enumerate(examples):
        filename = os.path.join(fname, f'task{i} example')
        with open(filename, 'w') as f:
            json.dump(task_example, f, indent=4)

    filename = os.path.join(fname, 'compo_task_example')
    with open(filename, 'w') as f:
        json.dump(compo_example, f, indent=4)

    filename = os.path.join(fname, 'frame_info')
    with open(filename, 'w') as f:
        json.dump(task_info.frame_info.dump(), f, indent=4)


def generate_temporal_example(max_memory, max_distractors, task_family,
                              whens=None, first_shareable=None):
    """
    generate 1 task objset and composition info object

    :param max_memory:
    :param max_distractors:
    :param task_family:
    :param whens:
    :param first_shareable:
    :return:
    """
    task = task_bank.random_task(task_family, whens, first_shareable)
    assert isinstance(task, tg.TemporalTask)

    # To get maximum memory duration, we need to specify the following average
    # memory value
    avg_mem = round(max_memory / 3.0 + 0.01, 2)
    if max_distractors == 0:
        objset = task.generate_objset(average_memory_span=avg_mem)
    else:
        objset = task.generate_objset(n_distractor=random.randint(1, max_distractors),
                                      average_memory_span=avg_mem)
    # Getting targets can remove some objects from objset.
    # Create example fields after this call.
    frame_info = ig.FrameInfo(task, objset)
    compo_info = ig.TaskInfoCompo(task, frame_info)
    return compo_info


def generate_compo_temporal_example(max_memory, max_distractors, families, n_tasks=1,
                                    *args, **kwargs):
    '''

    :param first_shareable:
    :param whens:
    :param families:
    :param max_memory:
    :param max_distractors:
    :param n_tasks:
    :return: combined TaskInfo Compo
    '''

    whens = kwargs.pop('whens', [None for _ in range(n_tasks)])

    if not isinstance(whens[0], list) and not None in whens:
        whens = [whens for _ in range(n_tasks)]
    if n_tasks == 1:
        return generate_temporal_example(max_memory, max_distractors, families, whens=whens[0], *args, **kwargs)

    compo_tasks = [generate_temporal_example(max_memory, max_distractors, families, whens=whens[i], *args, **kwargs)
                   for i in range(n_tasks)]
    # temporal combination
    cur_task = compo_tasks[0]
    for task in compo_tasks[1:]:
        cur_task.merge(task)
    return cur_task


# TODO: split training and validation after task generation

def generate_dataset(examples_per_family, output_dir='./data',
                     random_families=True, families=None,
                     composition=1, img_size=224,
                     train=0.7, validation=0.3, fixation_cue=True,
                     *args, **kwargs):
    if not random_families:
        assert families is not None
        assert composition == len(families)
    assert train + validation == 1.0
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    families_count = defaultdict(lambda: 0)
    if families is None or families == 'all':
        families = list(task_bank.task_family_dict.keys())
    print(families)
    n_families = len(families)
    total_examples = n_families * examples_per_family
    train_examples = total_examples * train
    validation_examples = total_examples * validation

    fam_str = '_'.join(families)
    if train != 0.7 and validation != 0.3:
        base_fname = os.path.join(output_dir,
                                  f'tasks_{fam_str}_{train}_{validation}')
    else:
        base_fname = os.path.join(output_dir,
                                  f'tasks_{fam_str}')

    train_fname = os.path.join(base_fname, 'train')
    validation_fname = os.path.join(base_fname, 'validation')

    if not os.path.exists(train_fname):
        os.makedirs(train_fname)
    if not os.path.exists(validation_fname):
        os.makedirs(validation_fname)

    if random_families:
        p = np.random.permutation(total_examples)
        i = 0
        while i < len(p):
            if i % 10000 == 0 and i > 0:
                print("Generated ", i, " examples")

            task_family = list()
            for j in range(composition):
                task_family.append(families[p[i] % n_families])
                families_count[families[p[i] % n_families]] += 1

            info = generate_compo_temporal_example(families=task_family, n_tasks=composition, *args, **kwargs)
            # Write the example randomly to training or validation folder
            split = bool(random.getrandbits(1))
            if (split or validation_examples <= 0) and train_examples > 0:
                train_examples -= 1
                fname = os.path.join(train_fname, f'{i}')
            else:
                validation_examples -= 1
                fname = os.path.join(validation_fname, f'{i}')

            write_task_instance(fname, info, img_size, fixation_cue)
            i += 1
    else:
        i = 0
        while i < total_examples:
            if i % 10000 == 0 and i > 0:
                print("Generated ", i, " examples")
            task_family = np.random.permutation(families)

            compo_tasks = [generate_temporal_example(task_family=[family], *args, **kwargs)
                           for family in task_family]
            # temporal combination
            info = compo_tasks[0]
            for task in compo_tasks[1:]:
                info.merge(task)

            # Write the example randomly to training or validation folder
            split = bool(random.getrandbits(1))
            if (split or validation_examples <= 0) and train_examples > 0:
                train_examples -= 1
                fname = os.path.join(train_fname, f'{i}')
            else:
                validation_examples -= 1
                fname = os.path.join(validation_fname, f'{i}')

            write_task_instance(fname, info, img_size, fixation_cue)
            i += 1
    return families_count


def main():
    args = get_args()
    print(args)

    const.DATA = const.Data(args.stim_dir)

    start = timeit.default_timer()
    if args.nback > 0:
        assert all('Compare' in family for family in args.families)
        whens = [f'last{args.nback}', 'last0']
        composition = args.nback_length - args.nback + 1
        generate_dataset(examples_per_family=args.examples_per_family, output_dir=args.output_dir,
                         composition=composition, img_size=args.img_size,
                         random_families=args.random_families, families=args.families,
                         train=args.training, validation=args.validation, fixation_cue=args.fixation_cue,
                         max_memory=args.max_memory, max_distractors=args.max_distractors,
                         whens=whens, first_shareable=1)
    elif args.seq_length > 0:
        first_shareable = 1

        if args.seq_reverse:
            # minimum 2 frames per DMS task
            if args.seq_length * 2 - 1 > const.MAX_MEMORY:
                raise ValueError('Not enough max memory')
            whens = [[f'last{const.MAX_MEMORY - (i * 2)}', 'last0'] for i in range(args.seq_length)]
        else:
            last_when = sg.random_when()
            while int(re.search(r'\d+', last_when).group()) - 1 < args.seq_length:
                last_when = sg.random_when()
            whens = [[last_when, 'last0'] for _ in range(args.seq_length)]
        generate_dataset(examples_per_family=args.examples_per_family, output_dir=args.output_dir,
                         composition=args.seq_length, img_size=args.img_size,
                         random_families=args.random_families, families=args.families,
                         train=args.training, validation=args.validation, fixation_cue=args.fixation_cue,
                         max_memory=args.max_memory, max_distractors=args.max_distractors,
                         whens=whens, first_shareable=first_shareable)
    else:
        whens = [None]
        if args.fix_delay:
            whens = [f'last{const.MAX_MEMORY}', 'last0']
        generate_dataset(examples_per_family=args.examples_per_family, output_dir=args.output_dir,
                         composition=args.composition, img_size=args.img_size,
                         random_families=args.random_families, families=args.families,
                         train=args.training, validation=args.validation, fixation_cue=args.fixation_cue,
                         max_memory=args.max_memory, max_distractors=args.max_distractors,
                         whens=whens, first_shareable=None)

    # # from task_bank.task_family_dict
    # tasks = ['CompareLoc', 'CompareObject', 'CompareCategory', 'CompareViewAngle']
    # task_combs = dict()
    # # generate all possible task combinations with specified i composition
    #
    # for i in range(1, 4):
    #     task_combs[i] = list(itertools.combinations_with_replacement(tasks, i))
    #
    # for i, task_comb in task_combs.items():
    #     for task_fam in task_comb:
    #         if i == 1:
    #             generate_dataset(max_memory, max_distractors,
    #                          1000, '/Users/markbai/Documents/School/COMP402/COG_v3/data/all_stims/no_comp',
    #                          composition=i, families=task_fam, random_families=False)
    #         else:
    #             generate_dataset(max_memory, max_distractors,
    #                              1000, f'/Users/markbai/Documents/School/COMP402/COG_v3/data/all_stims/comp_{i}',
    #                              composition=i, families=task_fam, random_families=False)
    # generate_dataset(max_memory, max_distractors,
    #                  50000, '/Users/markbai/Documents/School/COMP402/COG_v3/data/test',
    #                  composition=1, families=['CompareCategory'], train=0.7, validation=0.3)

    stop = timeit.default_timer()

    print('Time: ', stop - start)


if __name__ == '__main__':
    main()
