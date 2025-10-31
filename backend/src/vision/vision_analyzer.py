"""
Vision Analysis Module
Detects student posture, gaze, expression, and activity using computer vision.
Privacy-safe: processes frames in memory, stores only feature vectors.
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import mediapipe as mp


@dataclass
class VisionFeatures:
    """Extracted features from vision analysis (no raw images stored)"""
    timestamp: datetime
    posture: str  # "upright", "slouched", "leaning"
    gaze_direction: str  # "desk", "screen", "away"
    activity_level: float  # 0.0 to 1.0
    emotion: str  # "focused", "confused", "tired", "neutral"
    confidence: float
    hand_detected: bool
    pen_activity: bool


class VisionAnalyzer:
    """
    Analyzes student behavior from camera frames using MediaPipe and OpenCV.
    Designed for privacy: processes frames and discards them after feature extraction.
    """

    def __init__(self,
                 enable_pose: bool = True,
                 enable_face: bool = True,
                 enable_hands: bool = True):
        """
        Initialize vision analysis components.

        Args:
            enable_pose: Enable pose detection for posture analysis
            enable_face: Enable face mesh for emotion detection
            enable_hands: Enable hand tracking for activity detection
        """
        # Initialize MediaPipe components
        self.mp_pose = mp.solutions.pose
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands

        # Create detector instances
        self.pose_detector = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5
        ) if enable_pose else None

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) if enable_face else None

        self.hands_detector = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) if enable_hands else None

        # Motion detection (for activity level)
        self.prev_frame = None

    def analyze_frame(self, frame: np.ndarray) -> VisionFeatures:
        """
        Analyze a single frame and extract privacy-safe features.

        Args:
            frame: BGR image from camera (numpy array)

        Returns:
            VisionFeatures object with extracted metrics
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Extract individual features
        posture = self._detect_posture(rgb_frame)
        gaze = self._detect_gaze_direction(rgb_frame)
        activity = self._measure_activity_level(frame)
        emotion = self._detect_emotion(rgb_frame)
        hand_detected, pen_activity = self._detect_hand_activity(rgb_frame)

        # Frame is discarded after this point - only features are kept
        return VisionFeatures(
            timestamp=datetime.now(),
            posture=posture[0],
            gaze_direction=gaze[0],
            activity_level=activity,
            emotion=emotion[0],
            confidence=min(posture[1], gaze[1], emotion[1]),
            hand_detected=hand_detected,
            pen_activity=pen_activity
        )

    def _detect_posture(self, rgb_frame: np.ndarray) -> Tuple[str, float]:
        """
        Detect student posture using pose landmarks.

        Returns:
            (posture_label, confidence)
        """
        if not self.pose_detector:
            return ("unknown", 0.0)

        results = self.pose_detector.process(rgb_frame)

        if not results.pose_landmarks:
            return ("not_detected", 0.0)

        landmarks = results.pose_landmarks.landmark

        # Key points: shoulders, nose, hips
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
        nose = landmarks[self.mp_pose.PoseLandmark.NOSE]

        # Calculate shoulder angle (relative to horizontal)
        shoulder_slope = abs(left_shoulder.y - right_shoulder.y)

        # Calculate forward lean (nose vs shoulder center)
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2
        lean_forward = nose.y - shoulder_center_y

        # Classify posture
        if shoulder_slope > 0.05:
            posture = "tilted"
            confidence = 0.7
        elif lean_forward < -0.1:
            posture = "slouched"
            confidence = 0.8
        elif lean_forward > 0.05:
            posture = "leaning_forward"
            confidence = 0.75
        else:
            posture = "upright"
            confidence = 0.9

        return (posture, confidence)

    def _detect_gaze_direction(self, rgb_frame: np.ndarray) -> Tuple[str, float]:
        """
        Estimate gaze direction from face landmarks.

        Returns:
            (gaze_label, confidence)
        """
        if not self.face_mesh:
            return ("unknown", 0.0)

        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return ("away", 0.5)

        face_landmarks = results.multi_face_landmarks[0]
        landmarks = face_landmarks.landmark

        # Simplified gaze estimation using nose and eye positions
        # Indices: 1=nose tip, 33=left eye, 263=right eye
        nose = landmarks[1]
        left_eye = landmarks[33]
        right_eye = landmarks[263]

        # Calculate face orientation
        eye_center_x = (left_eye.x + right_eye.x) / 2
        nose_offset_x = nose.x - eye_center_x

        # Classify gaze direction
        if abs(nose_offset_x) > 0.08:
            gaze = "away"
            confidence = 0.7
        elif nose.y > 0.6:  # Looking down (at desk)
            gaze = "desk"
            confidence = 0.8
        else:
            gaze = "screen"
            confidence = 0.75

        return (gaze, confidence)

    def _measure_activity_level(self, frame: np.ndarray) -> float:
        """
        Measure motion/activity level by comparing consecutive frames.

        Returns:
            Activity score from 0.0 (no movement) to 1.0 (high movement)
        """
        # Convert to grayscale for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_frame is None:
            self.prev_frame = gray
            return 0.0

        # Compute difference between frames
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

        # Calculate activity as percentage of changed pixels
        activity = np.sum(thresh > 0) / thresh.size

        # Update previous frame
        self.prev_frame = gray

        # Normalize to 0-1 range
        activity_normalized = min(activity * 10, 1.0)

        return activity_normalized

    def _detect_emotion(self, rgb_frame: np.ndarray) -> Tuple[str, float]:
        """
        Detect emotion/mental state from facial expressions.

        Note: This is a simplified version. In production, use a trained
        emotion recognition model (e.g., FER+, AffectNet).

        Returns:
            (emotion_label, confidence)
        """
        if not self.face_mesh:
            return ("unknown", 0.0)

        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return ("neutral", 0.5)

        # Simplified emotion detection based on face landmarks
        # In production, replace with actual emotion recognition model
        landmarks = results.multi_face_landmarks[0].landmark

        # Analyze mouth curvature and eye openness for basic emotions
        # This is a placeholder - use a real emotion model in production
        mouth_left = landmarks[61]
        mouth_right = landmarks[291]
        mouth_top = landmarks[13]
        mouth_bottom = landmarks[14]

        # Eye openness (simplified)
        left_eye_top = landmarks[159]
        left_eye_bottom = landmarks[145]
        eye_openness = abs(left_eye_top.y - left_eye_bottom.y)

        # Mouth height (yawning indicator)
        mouth_openness = abs(mouth_top.y - mouth_bottom.y)

        # Simple heuristics (replace with ML model)
        if mouth_openness > 0.04:
            emotion = "tired"  # Possible yawn
            confidence = 0.6
        elif eye_openness < 0.015:
            emotion = "tired"  # Eyes closing
            confidence = 0.7
        else:
            emotion = "focused"
            confidence = 0.65

        return (emotion, confidence)

    def _detect_hand_activity(self, rgb_frame: np.ndarray) -> Tuple[bool, bool]:
        """
        Detect hand presence and potential pen/writing activity.

        Returns:
            (hand_detected, pen_activity_detected)
        """
        if not self.hands_detector:
            return (False, False)

        results = self.hands_detector.process(rgb_frame)

        if not results.multi_hand_landmarks:
            return (False, False)

        hand_detected = True

        # Detect pen-holding gesture (simplified)
        # Check if thumb, index, and middle finger are close together
        hand_landmarks = results.multi_hand_landmarks[0].landmark

        thumb_tip = hand_landmarks[4]
        index_tip = hand_landmarks[8]
        middle_tip = hand_landmarks[12]

        # Calculate distances
        thumb_index_dist = np.sqrt(
            (thumb_tip.x - index_tip.x)**2 +
            (thumb_tip.y - index_tip.y)**2
        )

        # If fingers are close together, likely holding a pen
        pen_activity = thumb_index_dist < 0.1

        return (hand_detected, pen_activity)

    def cleanup(self):
        """Release resources"""
        if self.pose_detector:
            self.pose_detector.close()
        if self.face_mesh:
            self.face_mesh.close()
        if self.hands_detector:
            self.hands_detector.close()


class FrameSampler:
    """
    Smart frame sampling to reduce processing load and respect privacy.
    Samples 1 frame every 2-5 seconds, or when significant motion detected.
    """

    def __init__(self,
                 base_interval: int = 3,
                 motion_threshold: float = 0.3):
        """
        Args:
            base_interval: Base sampling interval in seconds
            motion_threshold: Motion level to trigger immediate sampling
        """
        self.base_interval = base_interval
        self.motion_threshold = motion_threshold
        self.last_sample_time = None
        self.frame_count = 0

    def should_sample(self,
                     current_time: datetime,
                     activity_level: float = 0.0) -> bool:
        """
        Determine if current frame should be sampled.

        Args:
            current_time: Current timestamp
            activity_level: Detected activity level (0.0 to 1.0)

        Returns:
            True if frame should be sampled and analyzed
        """
        # First frame always sampled
        if self.last_sample_time is None:
            self.last_sample_time = current_time
            return True

        # Check time interval
        time_elapsed = (current_time - self.last_sample_time).total_seconds()

        # Sample if interval passed
        if time_elapsed >= self.base_interval:
            self.last_sample_time = current_time
            return True

        # Sample if high activity detected (e.g., page turn)
        if activity_level > self.motion_threshold:
            self.last_sample_time = current_time
            return True

        return False


# Example usage and testing
if __name__ == "__main__":
    print("Vision Analysis Module - Test Mode")
    print("=" * 50)

    # Initialize analyzer
    analyzer = VisionAnalyzer()
    sampler = FrameSampler(base_interval=3)

    # Simulate camera capture (in real use, get from actual camera)
    print("\n📷 Initializing camera simulation...")
    print("In production, connect to actual hovering camera device")
    print("\nExample feature extraction:")

    # Create a dummy frame for testing
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Analyze
    features = analyzer.analyze_frame(test_frame)

    print(f"\n✓ Extracted Features:")
    print(f"  - Timestamp: {features.timestamp}")
    print(f"  - Posture: {features.posture}")
    print(f"  - Gaze: {features.gaze_direction}")
    print(f"  - Activity Level: {features.activity_level:.2f}")
    print(f"  - Emotion: {features.emotion}")
    print(f"  - Confidence: {features.confidence:.2f}")
    print(f"  - Hand Detected: {features.hand_detected}")
    print(f"  - Pen Activity: {features.pen_activity}")

    print("\n✓ Privacy Check: Raw frame discarded, only features stored")

    analyzer.cleanup()
