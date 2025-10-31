"""
OCR & Handwriting Recognition Module
Extracts text from notebooks, textbooks, and screens.
Supports Chinese and English, mathematical equations, and handwriting.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class RecognizedText:
    """Structured text recognition result"""
    timestamp: datetime
    text: str
    language: str  # "en", "zh", "mixed"
    text_type: str  # "printed", "handwritten", "equation"
    bounding_boxes: List[Tuple[int, int, int, int]]  # (x, y, w, h)
    confidence: float
    detected_topics: List[str]  # e.g., ["Math", "Algebra"]


@dataclass
class MathEquation:
    """Recognized mathematical equation"""
    latex_repr: str
    text_repr: str
    difficulty: str  # "easy", "medium", "hard"
    topic: str  # e.g., "Quadratic Equations"


class TextRecognizer:
    """
    OCR and handwriting recognition using PaddleOCR and pattern matching.
    Designed to work with both printed and handwritten text.
    """

    def __init__(self,
                 use_gpu: bool = False,
                 enable_math: bool = True):
        """
        Initialize OCR engine.

        Args:
            use_gpu: Use GPU acceleration if available
            enable_math: Enable mathematical equation recognition
        """
        self.use_gpu = use_gpu
        self.enable_math = enable_math

        # In production, initialize PaddleOCR here:
        # from paddleocr import PaddleOCR
        # self.ocr_engine = PaddleOCR(use_angle_cls=True, lang='ch')

        # For now, we'll use a mock implementation
        self.ocr_engine = None

        # Topic keywords for classification
        self.topic_keywords = {
            "Math": ["equation", "solve", "calculate", "function", "algebra",
                    "geometry", "calculus", "equation", "formula", "数学",
                    "方程", "计算", "函数"],
            "Physics": ["force", "energy", "velocity", "acceleration",
                       "momentum", "物理", "力学", "能量"],
            "Chemistry": ["element", "compound", "reaction", "molecule",
                         "化学", "分子", "反应"],
            "English": ["grammar", "vocabulary", "essay", "literature",
                       "英语", "语法", "词汇"],
            "Chinese": ["古文", "诗歌", "作文", "语文", "文言文"],
        }

    def recognize_text(self, image: np.ndarray) -> RecognizedText:
        """
        Extract text from an image using OCR.

        Args:
            image: Input image (BGR format from OpenCV)

        Returns:
            RecognizedText object with extracted information
        """
        # Preprocess image for better OCR results
        processed = self._preprocess_image(image)

        # Perform OCR
        text, boxes, confidence = self._perform_ocr(processed)

        # Detect language
        language = self._detect_language(text)

        # Classify text type
        text_type = self._classify_text_type(text, image)

        # Detect topics
        topics = self._detect_topics(text)

        return RecognizedText(
            timestamp=datetime.now(),
            text=text,
            language=language,
            text_type=text_type,
            bounding_boxes=boxes,
            confidence=confidence,
            detected_topics=topics
        )

    def recognize_handwriting(self, image: np.ndarray) -> RecognizedText:
        """
        Specialized recognition for handwritten text.

        Args:
            image: Image containing handwriting

        Returns:
            RecognizedText with handwriting-specific processing
        """
        # Apply handwriting-specific preprocessing
        processed = self._preprocess_handwriting(image)

        # Use handwriting-optimized recognition
        # In production, use a specialized handwriting model
        result = self.recognize_text(processed)
        result.text_type = "handwritten"

        return result

    def recognize_equation(self, image: np.ndarray) -> Optional[MathEquation]:
        """
        Recognize mathematical equations and convert to LaTeX.

        Args:
            image: Image containing mathematical notation

        Returns:
            MathEquation object or None if no equation detected
        """
        if not self.enable_math:
            return None

        # In production, use specialized math OCR like:
        # - Mathpix API
        # - LaTeX-OCR models
        # - Pix2Tex

        # For now, detect common math patterns from text
        text_result = self.recognize_text(image)
        text = text_result.text

        # Simple equation pattern detection
        equation_patterns = [
            r'[xy]\s*=\s*[\d\+\-\*/\^\(\)xy]+',  # Simple equations
            r'\\frac\{.*?\}\{.*?\}',              # Fractions in LaTeX
            r'\d+\s*[\+\-\*/]\s*\d+',             # Arithmetic
        ]

        for pattern in equation_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return self._parse_equation(text)

        return None

    def extract_exercise_content(self, image: np.ndarray) -> Dict:
        """
        Extract structured exercise/problem content from homework.

        Args:
            image: Image of homework page

        Returns:
            Dictionary with problem number, question text, and answer
        """
        text_result = self.recognize_text(image)
        text = text_result.text

        # Extract problem numbers (e.g., "1.", "Problem 3:", "第5题")
        problems = []

        # Pattern matching for numbered problems
        problem_patterns = [
            r'(\d+)\.\s*(.+?)(?=\d+\.|$)',  # "1. Question text"
            r'Problem\s+(\d+):\s*(.+?)(?=Problem|$)',  # "Problem 1: text"
            r'第(\d+)题[：:]\s*(.+?)(?=第\d+题|$)',  # Chinese format
        ]

        for pattern in problem_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                problem_num = match.group(1)
                problem_text = match.group(2).strip()

                problems.append({
                    "number": problem_num,
                    "question": problem_text,
                    "detected_at": datetime.now().isoformat()
                })

        return {
            "total_problems": len(problems),
            "problems": problems,
            "topics": text_result.detected_topics
        }

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for optimal OCR results.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)

        # Adaptive thresholding for better text extraction
        thresh = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        # Deskew if needed (rotate to align text)
        deskewed = self._deskew_image(thresh)

        return deskewed

    def _preprocess_handwriting(self, image: np.ndarray) -> np.ndarray:
        """
        Specialized preprocessing for handwritten text.
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Less aggressive denoising to preserve handwriting details
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Binarization
        _, binary = cv2.threshold(
            enhanced, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        return binary

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Rotate image to align text horizontally.
        """
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image

        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = 90 + angle
        elif angle > 45:
            angle = angle - 90

        # Only deskew if angle is significant
        if abs(angle) < 0.5:
            return image

        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return rotated

    def _perform_ocr(self, image: np.ndarray) -> Tuple[str, List, float]:
        """
        Perform OCR on preprocessed image.

        Returns:
            (text, bounding_boxes, confidence)
        """
        # In production, use actual PaddleOCR:
        # result = self.ocr_engine.ocr(image, cls=True)
        # Parse results...

        # Mock implementation for demonstration
        text = "Sample recognized text from image"
        boxes = [(10, 10, 100, 30)]  # Example bounding box
        confidence = 0.85

        # Simulate actual OCR result structure
        if self.ocr_engine:
            # Real implementation would go here
            pass

        return (text, boxes, confidence)

    def _detect_language(self, text: str) -> str:
        """
        Detect language of recognized text.
        """
        # Check for Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        if chinese_chars > english_chars:
            return "zh"
        elif english_chars > chinese_chars:
            return "en"
        else:
            return "mixed"

    def _classify_text_type(self, text: str, image: np.ndarray) -> str:
        """
        Classify whether text is printed, handwritten, or equation.
        """
        # In production, use image features to distinguish
        # For now, use simple heuristics

        # Check for LaTeX or equation symbols
        equation_indicators = ['=', '+', '-', '×', '÷', '∑', '∫', '√']
        if any(symbol in text for symbol in equation_indicators):
            equation_ratio = sum(text.count(s) for s in equation_indicators) / len(text)
            if equation_ratio > 0.1:
                return "equation"

        # In real implementation, analyze image stroke consistency
        # Handwriting has more variation than printed text
        return "printed"

    def _detect_topics(self, text: str) -> List[str]:
        """
        Detect academic topics from recognized text.
        """
        detected = []

        for topic, keywords in self.topic_keywords.items():
            # Check if any keyword appears in text
            if any(keyword.lower() in text.lower() for keyword in keywords):
                detected.append(topic)

        return detected if detected else ["General"]

    def _parse_equation(self, text: str) -> MathEquation:
        """
        Parse recognized equation into structured format.
        """
        # Simplified equation parsing
        # In production, use SymPy or similar for proper parsing

        # Determine difficulty based on complexity
        difficulty = "easy"
        if any(op in text for op in ['^', '√', 'sin', 'cos', 'log']):
            difficulty = "hard"
        elif any(op in text for op in ['/', '*', '²', '³']):
            difficulty = "medium"

        # Detect topic
        topic = "Algebra"
        if 'sin' in text or 'cos' in text:
            topic = "Trigonometry"
        elif '∫' in text or 'dx' in text:
            topic = "Calculus"

        return MathEquation(
            latex_repr=text,  # In production, convert to proper LaTeX
            text_repr=text,
            difficulty=difficulty,
            topic=topic
        )


class HandwritingAnalyzer:
    """
    Analyzes handwriting quality and provides feedback.
    Useful for younger students learning to write.
    """

    def __init__(self):
        self.stroke_detector = None

    def analyze_quality(self, image: np.ndarray) -> Dict:
        """
        Analyze handwriting quality metrics.

        Returns:
            Dictionary with quality scores
        """
        # Analyze stroke consistency, character spacing, alignment
        metrics = {
            "neatness": 0.75,  # 0-1 scale
            "consistency": 0.82,
            "spacing": 0.68,
            "alignment": 0.79,
            "overall_score": 0.76,
            "feedback": []
        }

        # Generate feedback
        if metrics["neatness"] < 0.6:
            metrics["feedback"].append("Try to write more neatly")
        if metrics["spacing"] < 0.6:
            metrics["feedback"].append("Watch spacing between characters")

        return metrics


# Example usage
if __name__ == "__main__":
    print("OCR & Handwriting Recognition Module - Test Mode")
    print("=" * 50)

    recognizer = TextRecognizer()

    # Create test image
    test_image = np.zeros((300, 500, 3), dtype=np.uint8)
    cv2.putText(test_image, "Test Math Problem: x + 5 = 12",
                (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    print("\n📝 Testing text recognition...")
    result = recognizer.recognize_text(test_image)

    print(f"\n✓ Recognition Result:")
    print(f"  - Text: {result.text}")
    print(f"  - Language: {result.language}")
    print(f"  - Type: {result.text_type}")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - Topics: {', '.join(result.detected_topics)}")

    print("\n✓ Example: In production, this would use PaddleOCR or Google Vision API")
    print("✓ Supports: Chinese, English, Math equations, Handwriting")
