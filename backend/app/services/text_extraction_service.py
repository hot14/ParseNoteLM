"""
음성 및 텍스트 추출 서비스 모듈
"""

import os
import logging
import tempfile
import whisper
import cv2
import easyocr
import pytesseract
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class SpeechToTextService:
    """음성을 텍스트로 변환하는 서비스"""
    
    def __init__(self, model_size: str = "base"):
        """
        음성 인식 서비스 초기화
        
        Args:
            model_size: Whisper 모델 크기 (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Whisper 모델 로드"""
        try:
            logger.info(f"Whisper 모델 로드 중: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            logger.info("Whisper 모델 로드 완료")
        except Exception as error:
            logger.error(f"Whisper 모델 로드 실패: {error}")
            raise
    
    def transcribe_audio(self, audio_path: str, language: str = "ko") -> Optional[Dict[str, Any]]:
        """
        오디오 파일을 텍스트로 변환
        
        Args:
            audio_path: 오디오 파일 경로
            language: 언어 코드 (ko, en 등)
            
        Returns:
            변환 결과 딕셔너리 또는 None
        """
        try:
            if not os.path.exists(audio_path):
                logger.error(f"오디오 파일이 존재하지 않습니다: {audio_path}")
                return None
            
            logger.info(f"음성 인식 시작: {audio_path}")
            
            # Whisper로 음성 인식 수행
            result = self.model.transcribe(
                audio_path,
                language=language,
                verbose=True
            )
            
            # 결과 정리
            transcription_result = {
                "text": result["text"].strip(),
                "language": result["language"],
                "segments": []
            }
            
            # 세그먼트 정보 추가
            for segment in result["segments"]:
                transcription_result["segments"].append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip()
                })
            
            logger.info(f"음성 인식 완료: {len(transcription_result['segments'])}개 세그먼트")
            return transcription_result
            
        except Exception as error:
            logger.error(f"음성 인식 실패: {error}")
            return None
    
    def get_supported_languages(self) -> List[str]:
        """지원되는 언어 목록 반환"""
        return list(whisper.tokenizer.LANGUAGES.keys())


class OCRService:
    """이미지에서 텍스트를 추출하는 OCR 서비스"""
    
    def __init__(self, use_easyocr: bool = True):
        """
        OCR 서비스 초기화
        
        Args:
            use_easyocr: EasyOCR 사용 여부 (False면 Tesseract 사용)
        """
        self.use_easyocr = use_easyocr
        self.easyocr_reader = None
        
        if use_easyocr:
            self._init_easyocr()
    
    def _init_easyocr(self):
        """EasyOCR 초기화"""
        try:
            logger.info("EasyOCR 초기화 중...")
            self.easyocr_reader = easyocr.Reader(['ko', 'en'])
            logger.info("EasyOCR 초기화 완료")
        except Exception as error:
            logger.error(f"EasyOCR 초기화 실패: {error}")
            raise
    
    def extract_text_from_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        이미지에서 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            추출된 텍스트 정보 딕셔너리 또는 None
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"이미지 파일이 존재하지 않습니다: {image_path}")
                return None
            
            if self.use_easyocr:
                return self._extract_with_easyocr(image_path)
            else:
                return self._extract_with_tesseract(image_path)
                
        except Exception as error:
            logger.error(f"텍스트 추출 실패: {error}")
            return None
    
    def _extract_with_easyocr(self, image_path: str) -> Dict[str, Any]:
        """EasyOCR을 사용한 텍스트 추출"""
        results = self.easyocr_reader.readtext(image_path)
        
        extracted_texts = []
        full_text = ""
        
        for (bbox, text, confidence) in results:
            if confidence > 0.5:  # 신뢰도 임계값
                extracted_texts.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox
                })
                full_text += text + " "
        
        return {
            "full_text": full_text.strip(),
            "texts": extracted_texts,
            "method": "easyocr"
        }
    
    def _extract_with_tesseract(self, image_path: str) -> Dict[str, Any]:
        """Tesseract를 사용한 텍스트 추출"""
        # 이미지 로드 및 전처리
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 텍스트 추출
        config = '--oem 3 --psm 6 -l kor+eng'
        text = pytesseract.image_to_string(gray, config=config)
        
        # 상세 정보 추출
        data = pytesseract.image_to_data(gray, config=config, output_type=pytesseract.Output.DICT)
        
        extracted_texts = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 30:  # 신뢰도 임계값
                text_item = data['text'][i].strip()
                if text_item:
                    extracted_texts.append({
                        "text": text_item,
                        "confidence": int(data['conf'][i]) / 100.0,
                        "bbox": [
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        ]
                    })
        
        return {
            "full_text": text.strip(),
            "texts": extracted_texts,
            "method": "tesseract"
        }
    
    def extract_text_from_frames(self, frame_paths: List[str]) -> Dict[str, Any]:
        """
        여러 프레임에서 텍스트 추출
        
        Args:
            frame_paths: 프레임 이미지 파일 경로 리스트
            
        Returns:
            모든 프레임의 텍스트 추출 결과
        """
        all_texts = []
        frame_results = []
        
        for i, frame_path in enumerate(frame_paths):
            logger.info(f"프레임 {i+1}/{len(frame_paths)} 텍스트 추출 중...")
            
            result = self.extract_text_from_image(frame_path)
            if result and result["full_text"]:
                frame_results.append({
                    "frame_index": i,
                    "frame_path": frame_path,
                    "result": result
                })
                all_texts.append(result["full_text"])
        
        # 중복 제거 및 정리
        unique_texts = list(set(all_texts))
        combined_text = " ".join(unique_texts)
        
        return {
            "combined_text": combined_text,
            "unique_texts": unique_texts,
            "frame_results": frame_results,
            "total_frames": len(frame_paths),
            "frames_with_text": len(frame_results)
        }


class VideoTextExtractionService:
    """비디오에서 음성과 텍스트를 모두 추출하는 통합 서비스"""
    
    def __init__(self, whisper_model: str = "base", use_easyocr: bool = True):
        """
        비디오 텍스트 추출 서비스 초기화
        
        Args:
            whisper_model: Whisper 모델 크기
            use_easyocr: EasyOCR 사용 여부
        """
        self.speech_service = SpeechToTextService(whisper_model)
        self.ocr_service = OCRService(use_easyocr)
    
    def extract_all_text_from_video(self, video_path: str, audio_path: str, 
                                  frame_paths: List[str]) -> Dict[str, Any]:
        """
        비디오에서 음성과 화면 텍스트를 모두 추출
        
        Args:
            video_path: 비디오 파일 경로
            audio_path: 추출된 오디오 파일 경로
            frame_paths: 추출된 프레임 이미지 경로 리스트
            
        Returns:
            통합 텍스트 추출 결과
        """
        logger.info("비디오 텍스트 추출 시작")
        
        # 음성 인식
        speech_result = self.speech_service.transcribe_audio(audio_path)
        
        # 화면 텍스트 추출
        ocr_result = self.ocr_service.extract_text_from_frames(frame_paths)
        
        # 결과 통합
        result = {
            "video_path": video_path,
            "speech_transcription": speech_result,
            "screen_text_extraction": ocr_result,
            "combined_content": {
                "speech_text": speech_result["text"] if speech_result else "",
                "screen_text": ocr_result["combined_text"] if ocr_result else "",
                "total_content": ""
            }
        }
        
        # 전체 내용 결합
        all_content = []
        if speech_result and speech_result["text"]:
            all_content.append(f"[음성 내용]\n{speech_result['text']}")
        
        if ocr_result and ocr_result["combined_text"]:
            all_content.append(f"[화면 텍스트]\n{ocr_result['combined_text']}")
        
        result["combined_content"]["total_content"] = "\n\n".join(all_content)
        
        logger.info("비디오 텍스트 추출 완료")
        return result


def create_speech_to_text_service(model_size: str = "base") -> SpeechToTextService:
    """음성 인식 서비스 인스턴스 생성"""
    return SpeechToTextService(model_size)


def create_ocr_service(use_easyocr: bool = True) -> OCRService:
    """OCR 서비스 인스턴스 생성"""
    return OCRService(use_easyocr)


def create_video_text_extraction_service(whisper_model: str = "base", 
                                       use_easyocr: bool = True) -> VideoTextExtractionService:
    """비디오 텍스트 추출 서비스 인스턴스 생성"""
    return VideoTextExtractionService(whisper_model, use_easyocr)

