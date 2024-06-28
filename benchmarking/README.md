# Benchmarking Run Parameters

### Single Frame Example

```shell
conda activate iwisdm
python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/single_cat' --trials_dir='temp/single_cat' --config_path='configs/single_frame_cat.json' --min_len=1 --max_len=1 --n_trials=100 --n_tasks=10 --features='cat' --min_joint_ops=0 --max_joint_ops=0 --force_balance
```

### Low Complexity Example:

```shell
conda activate iwisdm
python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/low_all' --trials_dir='temp/low_all' --config_path='configs/low_complexity_all.json' --min_len=6 --max_len=6  --n_trials=100 --n_tasks=100 --features='all' --min_joint_ops=1 --max_joint_ops=1 --force_balance
```

### Medium Complexity Example:

```shell
conda activate iwisdm
python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/medium_all' --trials_dir='temp/medium_all' --config_path='configs/medium_complexity_all.json' --min_len=8 --max_len=8 --n_trials=100 --n_tasks=100 --features='all' --min_joint_ops=1 --max_joint_ops=1 --force_balance
```

### High Complexity Example:

```shell
conda activate iwisdm
python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/high_all' --trials_dir='temp/high_all' --config_path='configs/high_complexity_all.json' --min_len=9 --max_len=9 --n_trials=100 --n_tasks=100 --features='all' --min_joint_ops=1 --max_joint_ops=2 --force_balance --non_bool_actions
```

## iWISDM+:

1. Memory: task difficulty is varied by changing the number of delay frames
   a. 1frame tasks: report of object property after delay (location or category)
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/memory_1_frame' --trials_dir='temp/memory_1_frame' --config_path='configs/single_frame_cat.json' --min_len=3 --max_len=10 --n_trials=10 --n_tasks=10 --features='cat' --min_joint_ops=0 --max_joint_ops=0 --force_balance
    ```
   b. 2frame tasks: compare two object properties with delay either in between or afterward (location, category,
   identity)
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/memory_2_frame' --trials_dir='temp/memory_2_frame' --config_path='configs/low_complexity_cat.json' --min_len=3 --max_len=10 --n_trials=10 --n_tasks=10 --features='cat' --min_joint_ops=0 --max_joint_ops=0 --force_balance
    ```
    *the max_joint_ops may should be set to 0 to avoid and, or in the instructions*
2. Object localization:
   a. 1frame: report location
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/localization_1_frame' --trials_dir='temp/localization_1_frame' --config_path='configs/high_complexity_loc_noswitch.json' --min_len=1 --max_len=1 --n_trials=100 --n_tasks=10 --features='loc' --min_joint_ops=0 --max_joint_ops=0 --non_bool_actions
    ```
   b. 2frames: comparison based on location
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/localization_2_frame' --trials_dir='temp/localization_2_frame' --config_path='configs/low_complexity_loc.json' --min_len=2 --max_len=2 --n_trials=10 --n_tasks=1 --features='loc' --min_joint_ops=0 --max_joint_ops=1 --force_balance
    ```
3. Object categorization: similar to above but based on category  
   a. 1frame: report category
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/categorization_1_frame' --trials_dir='temp/categorization_1_frame' --config_path='configs/single_frame_cat.json' --min_len=1 --max_len=1 --n_trials=10 --n_tasks=10 --features='cat' --min_joint_ops=0 --max_joint_ops=0 --force_balance
    ```
   b. 2frames: comparison based on category
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/categorization_2_frame' --trials_dir='temp/categorization_2_frame' --config_path='configs/low_complexity_cat.json' --min_len=2 --max_len=2 --n_trials=10 --n_tasks=10 --features='cat' --min_joint_ops=0 --max_joint_ops=1 --force_balance
    ```
4. Spatial attention:
   a. 1frame with distractor. Report object category
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/spatial_attn_1_frame' --trials_dir='temp/spatial_attn_1_frame' --config_path='configs/single_frame_cat.json' --min_len=1 --max_len=1 --n_trials=10 --n_tasks=10 --features='cat' --min_joint_ops=0 --max_joint_ops=0 --force_balance --n_distractor_frame=1
    ```
   b. 2frame tasks with distractors on both. The tasks are based on category (or identity) information, so objects are
   identified by their location information where instruction specifies which object on each frame is to be attended to
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/spatial_attn_2_frame' --trials_dir='temp/spatial_attn_2_frame' --config_path='configs/low_complexity_cat.json' --min_len=2 --max_len=2 --n_trials=10 --n_tasks=10 --features='cat' --min_joint_ops=0 --max_joint_ops=1 --force_balance --n_distractor_frame=2
    ```
5. Feature attention: similar to above but the tasks are based on location information, so objects are identified by
   their category information
   a. 1 frame
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/feature_attn_1_frame' --trials_dir='temp/feature_attn_1_frame' --config_path='configs/single_frame_loc.json' --min_len=1 --max_len=1 --n_trials=10 --n_tasks=10 --features='loc' --min_joint_ops=0 --max_joint_ops=0 --force_balance --n_distractor_frame=1
    ```
   b. 2 frame
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/feature_attn_2_frame' --trials_dir='temp/feature_attn_2_frame' --config_path='configs/low_complexity_loc.json' --min_len=2 --max_len=2 --n_trials=10 --n_tasks=10 --features='loc' --min_joint_ops=0 --max_joint_ops=1 --force_balance --n_distractor_frame=2
    ```
6. Temporal attention: 2 frames or more.
   a. 1frame decisions: report of object property (location or category) when there are other distractor frames
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/temporal_attn_1_frame_cat' --trials_dir='temp/temporal_attn_1_frame_cat' --config_path='configs/single_frame_cat.json' --min_len=2 --max_len=2 --n_trials=10 --n_tasks=10 --features='cat' --min_joint_ops=0 --max_joint_ops=0 --force_balance --n_distractor_time=1
    ```
   b. 2frame decisions: comparison between two objects when there are other distractor frames (location, category,
   identity)
    ```shell
    conda activate iwisdm
    python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/temporal_attn_2_frame_cat' --trials_dir='temp/temporal_attn_2_frame_cat' --config_path='configs/low_complexity_cat.json' --min_len=6 --max_len=10 --n_trials=10 --n_tasks=10 --features='cat' --min_joint_ops=0 --max_joint_ops=1 --force_balance --n_distractor_time=2
    ```
7. Logical reasoning: similar to main iwisdm assessments where we generate random tasks and categorize them to levels of
   complexity according to factors such as number of frames, number of operations, number of switches etc (refer to
   iwisdm paper)
   (probably version with image&without image
    ```shell
   conda activate iwisdm
   python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/logical' --trials_dir='temp/logical' --config_path='configs/high_complexity_all.json' --min_len=9 --max_len=9 --n_trials=10 --n_tasks=10 --features='all' --min_joint_ops=1 --max_joint_ops=2 --force_balance --non_bool_actions
    ```
