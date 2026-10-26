"""
Full Vocabulary Canonical Dataset Generator & Augmentation Pipeline
Synthesizes and augments realistic 3D landmark configurations for all 26 ASL alphabet
letters and key conversational phrases, producing a comprehensive multi-class ML dataset.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pickle
import numpy as np
from src.text_to_sign import TextToSignEngine



def generate_variations(base_coords_21x3: np.ndarray, num_samples: int = 180, noise_level: float = 0.022):
    """
    Applies 3D spatial perturbations to base landmark geometry:
    - 3D Gaussian noise on joint positions
    - Euler 3D rotations (Yaw, Pitch, Roll jitter)
    - Scale perturbations and invariant re-normalization
    """
    samples = []
    base_3d = base_coords_21x3.copy()

    # Pre-normalize base
    base_3d = base_3d - base_3d[0]
    scale_0 = np.linalg.norm(base_3d[9])
    if scale_0 > 1e-4:
        base_3d = base_3d / scale_0

    for _ in range(num_samples):
        # 1. Coordinate noise
        noise = np.random.normal(0, noise_level, base_3d.shape)
        noisy = base_3d + noise

        # 2. 3D Rotation jitter (Yaw/Z, Pitch/X, Roll/Y)
        tz = np.radians(np.random.uniform(-10, 10))
        cz, sz = np.cos(tz), np.sin(tz)
        rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])

        tx = np.radians(np.random.uniform(-7, 7))
        cx, sx = np.cos(tx), np.sin(tx)
        rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])

        ty = np.radians(np.random.uniform(-7, 7))
        cy, sy = np.cos(ty), np.sin(ty)
        ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])

        rot = np.dot(np.dot(np.dot(noisy, rz.T), rx.T), ry.T)

        # 3. Scale jitter
        scale_f = np.random.uniform(0.93, 1.07)
        scaled = rot * scale_f

        # 4. Strict origin and scale invariant re-normalization
        scaled = scaled - scaled[0]
        ref_norm = np.linalg.norm(scaled[9] - scaled[0])
        if ref_norm > 1e-4:
            scaled = scaled / ref_norm

        samples.append(scaled.flatten().astype(np.float32))

    return samples


def build_full_dataset():
    dataset_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(dataset_dir, exist_ok=True)
    dataset_path = os.path.join(dataset_dir, "landmarks_dataset.pickle")

    all_data = []
    all_labels = []

    # 1. Load existing real collected samples if present
    if os.path.exists(dataset_path):
        try:
            with open(dataset_path, 'rb') as f:
                d = pickle.load(f)
                all_data = list(d.get('data', []))
                all_labels = list(d.get('labels', []))
            print(f"[Dataset] Preserved {len(all_data)} existing baseline samples across {len(set(all_labels))} classes.")
        except Exception as e:
            print(f"[Dataset] Note: Could not load previous dataset: {e}")

    existing_classes = set(all_labels)

    # 2. Comprehensive Vocabulary Dictionary
    full_vocabulary = [
        # Full ASL Alphabet A-Z
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        # Social & Conversational Signs
        'HELLO', 'THANK YOU', 'YES', 'NO', 'HELP', 'WATER', 'I LOVE YOU',
        'OK', 'PEACE', 'CALL', 'PLEASE', 'GOOD', 'BAD', 'FOOD', 'STOP'
    ]

    t2s = TextToSignEngine()
    added_count = 0

    print(f"[Dataset] Generating augmented landmark samples for full vocabulary ({len(full_vocabulary)} classes)...")

    for sign in full_vocabulary:
        # Check if sign needs generation or augmentation
        curr_count = sum(1 for l in all_labels if l == sign)
        needed = max(0, 180 - curr_count)

        if needed > 0:
            pose_21x3 = t2s.generate_landmark_pose(sign)
            variations = generate_variations(pose_21x3, num_samples=needed)
            all_data.extend(variations)
            all_labels.extend([sign] * len(variations))
            added_count += len(variations)

    print(f"[Dataset] Successfully added {added_count} new synthetic/augmented samples.")
    print(f"[Dataset] Total combined dataset size: {len(all_data)} samples across {len(set(all_labels))} classes.")

    # Save to landmarks_dataset.pickle
    with open(dataset_path, 'wb') as f:
        pickle.dump({'data': np.array(all_data), 'labels': np.array(all_labels)}, f)

    print(f"[Dataset] Exported full multi-class dataset to {dataset_path}!")


if __name__ == "__main__":
    build_full_dataset()
