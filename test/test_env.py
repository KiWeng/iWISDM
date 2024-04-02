import unittest
from wisdom import make
from wisdom import read_write


class MyTestCase(unittest.TestCase):
    def test_env(self):
        env = make(
            env_id='ShapeNet',
            dataset_fp='/Users/markbai/Documents/COG_v3_shapenet/data/shapenet_handpicked_val'
        )
        print(env.env_spec.auto_gen_config)
        tasks = env.generate_tasks(100)
        for t in tasks:
            _, (_, temporal_task) = t
            trials = env.generate_trials(tasks=[temporal_task], mode='valid')
            # read_write.write_trial()
        # TODO: stimuli sampled from dataset splits, have 3 separate df files?
        #  self.stim_data.train = SNStimData(), etc
        env.get_premade_task()
        return


if __name__ == '__main__':
    unittest.main()
