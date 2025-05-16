import cv2
import numpy as np
import os
from datetime import datetime
import time

class MotionDetector:
    def __init__(self, video_path, output_dir='output', threshold=500, min_contour_area=500, min_duration=1.0):
        """
        움직임 감지기 초기화
        
        :param video_path: 분석할 비디오 파일 경로 (0을 입력하면 웹캠 사용)
        :param output_dir: 출력 디렉토리
        :param threshold: 움직임 감지 임계값 (픽셀 차이의 합)
        :param min_contour_area: 움직임으로 인식할 최소 컨투어 면적
        :param min_duration: 저장할 최소 움직임 지속 시간(초)
        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.threshold = threshold
        self.min_contour_area = min_contour_area
        self.min_duration = min_duration
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 비디오 캡처 객체 생성 (웹캠 또는 비디오 파일)
        if str(video_path).isdigit():
            self.cap = cv2.VideoCapture(int(video_path))
        else:
            self.cap = cv2.VideoCapture(video_path)
            
        if not self.cap.isOpened():
            raise ValueError(f"비디오 소스를 열 수 없습니다: {video_path}")
        
        # 비디오 정보 가져오기
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        # 웹캠의 경우 기본 FPS가 0일 수 있으므로 기본값 설정
        if self.fps <= 0:
            self.fps = 30  # 기본 FPS 값
            
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 출력 비디오 파일 설정
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_video = os.path.join(output_dir, f"motion_detected_{timestamp}.mp4")
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter(
            self.output_video, 
            self.fourcc, 
            self.fps, 
            (self.width, self.height)
        )
        
        # 상태 변수 초기화
        self.motion_detected = False
        self.motion_start_time = 0
        self.frame_count = 0
        self.motion_boxes = []  # 움직임 영역을 저장할 리스트
    
    def detect_motion(self, frame1, frame2):
        """두 프레임 간의 움직임 감지 및 움직임 영역 반환"""
        # 그레이스케일로 변환
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # 가우시안 블러 적용 (노이즈 제거)
        gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
        gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
        
        # 프레임 간 차이 계산
        frame_delta = cv2.absdiff(gray1, gray2)
        _, thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)
        
        # 모폴로지 연산으로 노이즈 제거
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # 컨투어 찾기
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 움직임 영역의 바운딩 박스 계산
        motion_boxes = []
        motion_detected = False
        
        for contour in contours:
            if cv2.contourArea(contour) > self.min_contour_area:
                motion_detected = True
                # 컨투어를 둘러싸는 사각형 좌표 얻기
                (x, y, w, h) = cv2.boundingRect(contour)
                motion_boxes.append((x, y, x + w, y + h))  # (x1, y1, x2, y2) 형식으로 저장
        
        return motion_detected, motion_boxes
    
    def draw_boxes(self, frame, boxes):
        """프레임에 움직임 영역에 사각형 그리기"""
        for (x1, y1, x2, y2) in boxes:
            # 빨간색 사각형 그리기 (BGR 색상)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            
            # 상단에 'Motion' 텍스트 표시
            cv2.putText(frame, 'Motion', (x1, y1 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        return frame
    
    def process_video(self):
        """비디오 처리 및 움직임 감지"""
        print(f"비디오 처리 시작: {self.video_path}")
        print(f"해상도: {self.width}x{self.height}, FPS: {self.fps}")
        print(f"출력 파일: {self.output_video}")
        print("'q' 키를 누르면 종료됩니다.")
        
        ret, frame1 = self.cap.read()
        if not ret:
            print("비디오를 읽을 수 없습니다.")
            return
            
        ret, frame2 = self.cap.read()
        
        prev_time = time.time()
        frame_count = 0
        fps_text = "FPS: 0"
        
        while ret:
            self.frame_count += 1
            frame_count += 1
            
            # FPS 계산 (1초마다 업데이트)
            current_time = time.time()
            if current_time - prev_time >= 1.0:
                fps = frame_count / (current_time - prev_time)
                fps_text = f"FPS: {fps:.1f}"
                prev_time = current_time
                frame_count = 0
            
            # 움직임 감지
            motion_detected, motion_boxes = self.detect_motion(frame1, frame2)
            
            # 움직임이 감지된 경우
            if motion_detected:
                current_time_sec = self.frame_count / self.fps
                
                # 새로운 움직임이 시작된 경우
                if not self.motion_detected:
                    self.motion_detected = True
                    self.motion_start_time = current_time_sec
                    print(f"움직임 감지 시작: {current_time_sec:.2f}초")
                
                # 움직임 영역에 사각형 그리기
                frame_with_boxes = self.draw_boxes(frame2.copy(), motion_boxes)
                
                # FPS 텍스트 추가
                cv2.putText(frame_with_boxes, fps_text, (10, 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 결과 비디오에 프레임 쓰기
                self.out.write(frame_with_boxes)
                
                # 화면에 표시
                cv2.imshow('Motion Detection', frame_with_boxes)
            
            # 움직임이 없는 경우
            else:
                # FPS 텍스트만 추가
                frame_with_text = frame2.copy()
                cv2.putText(frame_with_text, fps_text, (10, 30), 
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # 결과 비디오에 프레임 쓰기 (움직임이 없어도 모든 프레임 저장)
                self.out.write(frame_with_text)
                
                # 화면에 표시
                cv2.imshow('Motion Detection', frame_with_text)
                
                # 움직임이 끝난 경우
                if self.motion_detected:
                    current_time_sec = self.frame_count / self.fps
                    motion_duration = current_time_sec - self.motion_start_time
                    
                    # 최소 지속 시간을 넘은 경우에만 저장
                    if motion_duration >= self.min_duration:
                        print(f"움직임 감지 종료: {current_time_sec:.2f}초, 지속 시간: {motion_duration:.2f}초")
                    
                    self.motion_detected = False
            
            # 다음 프레임으로 이동
            frame1 = frame2
            ret, frame2 = self.cap.read()
            
            # 'q' 키를 누르면 종료
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        # 자원 해제
        self.cap.release()
        self.out.release()
        cv2.destroyAllWindows()
        
        print("\n비디오 처리 완료!")
        print(f"결과 파일이 저장되었습니다: {self.output_video}")
    
    def start_new_clip(self):
        """새로운 클립 녹화 시작 (이전 버전 호환성을 위해 유지)"""
        pass
    
    def close_clip(self):
        """현재 녹화 중인 클립 닫기 (이전 버전 호환성을 위해 유지)"""
        pass


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='CCTV 영상에서 움직임이 있는 구간을 자동으로 감지하고 저장합니다.')
    parser.add_argument('video_path', help='분석할 비디오 파일 경로 (웹캠을 사용하려면 0 또는 1 입력)')
    parser.add_argument('--output', '-o', default='output', help='출력 디렉토리 (기본값: output/)')
    parser.add_argument('--threshold', '-t', type=int, default=500, 
                        help='움직임 감지 임계값 (기본값: 500, 낮을수록 민감)')
    parser.add_argument('--min-area', type=int, default=500,
                        help='움직임으로 인식할 최소 컨투어 면적 (기본값: 500)')
    parser.add_argument('--min-duration', type=float, default=1.0,
                        help='저장할 최소 움직임 지속 시간(초) (기본값: 1.0)')
    
    args = parser.parse_args()
    
    # 움직임 감지기 생성 및 실행
    try:
        detector = MotionDetector(
            video_path=args.video_path,
            output_dir=args.output,
            threshold=args.threshold,
            min_contour_area=args.min_area,
            min_duration=args.min_duration
        )
        detector.process_video()
    except KeyboardInterrupt:
        print("\n사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
