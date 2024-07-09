from scipy.spatial.transform import Rotation as R, Slerp
import numpy as np
from scipy.interpolate import interp1d

class PoseLoader:
    def __init__(self):
        self.poses = []

    def generate(self, landmarks):
        landmarks = sorted(landmarks, key=lambda lm: lm['frame_number'])
        frame_numbers = [lm['frame_number'] for lm in landmarks]
        positions = np.array([lm['transform'] for lm in landmarks])
        rotations = R.from_quat([lm['quaternion'] for lm in landmarks])
        slerp = Slerp(frame_numbers, rotations)
        lerp = interp1d(frame_numbers, positions, axis=0, kind='linear', fill_value="extrapolate")
        
        for fnum in range(frame_numbers[0], frame_numbers[-1] + 1):
            transform = lerp(fnum).tolist()  
            quaternion = slerp(fnum).as_quat().tolist()
            self.poses.append({
                'frame_number': fnum,
                'quaternion': quaternion,
                'position': transform,
                'rms_error': 0,
            })

    def get_transform(self, frame_number):
        pose = self.poses[frame_number]
        if pose:
            return pose
        else:
            return {
                'quaternion' : [1, 0, 0, 0],
                'transform' : [0, 0, 0],
                'rms_error' : 0,
            }