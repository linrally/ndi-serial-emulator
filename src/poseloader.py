from scipy.spatial.transform import Rotation as R, Slerp
import numpy as np
from scipy.interpolate import interp1d

class PoseLoader:
    def __init__(self, all_landmarks):
        self.poses = {}

        for handle_id, landmarks in all_landmarks.items():
            handle_poses = []

            landmarks = sorted(landmarks, key=lambda lm: lm['frame_number'])
            frame_numbers = [lm['frame_number'] for lm in landmarks]
            positions = np.array([lm['transform'] for lm in landmarks])
            rotations = R.from_quat([lm['quaternion'] for lm in landmarks])
            slerp = Slerp(frame_numbers, rotations)
            lerp = interp1d(frame_numbers, positions, axis=0, kind='linear', fill_value="extrapolate")
            
            for fnum in range(frame_numbers[0], frame_numbers[-1] + 1):
                transform = lerp(fnum).tolist()  
                quaternion = slerp(fnum).as_quat().tolist()
                handle_poses.append({
                    'frame_number': fnum,
                    'quaternion': quaternion,
                    'transform': transform,
                    'rms_error': 0,
                })        

            self.poses[handle_id] = handle_poses

    def get_transform(self, handle_id, frame_number):
        pose = self.poses[handle_id][frame_number]
        if pose:
            return pose
        else:
            return {
                'quaternion' : [0, 0, 0, 1],
                'transform' : [0, 0, 0],
                'rms_error' : 0,
            }