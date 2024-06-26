when min_joint_ops=0 && max_joint_ops=0 it can generate only 2 trials and stuck in a infinite loop 

```shell
conda activate iwisdm
python create_bench.py --stim_dir='../data/shapenet_handpicked' --tasks_dir='./tasks/localization_2_frame' --trials_dir='temp/localization_2_frame' --config_path='configs/low_complexity_loc.json' --min_len=2 --max_len=2 --n_trials=10 --n_tasks=10 --features='loc' --min_joint_ops=0 --max_joint_ops=0 --force_balance
```
