✅ 프로젝트 개요
목표: CCTV 같은 장시간 영상에서 움직임이 있는 구간만 추출하여 사람이 검토할 수 있도록 하는 도구

✅ 주요 기능 구성 (AI 없이 가능)
기능	설명
프레임 간 차이 비교	이전 프레임과 현재 프레임을 비교하여 변화량 측정
움직임 여부 판단	차이값이 일정 임계치를 넘으면 움직임 발생으로 판단
중요 구간 저장	움직임이 있는 프레임 또는 영상 클립 저장 (예: mp4)
프리뷰 생성	썸네일이나 구간 리스트 생성 (간단한 영상 요약)
✅ 사용할 기술 (예시: Python + OpenCV)
1. 프레임 차이 계산
```python
import cv2

cap = cv2.VideoCapture('cctv_video.mp4')
ret, frame1 = cap.read()
ret, frame2 = cap.read()

while ret:
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        print("움직임 감지됨!")

    frame1 = frame2
    ret, frame2 = cap.read()

```
2. 움직임이 있을 때만 영상 저장 (구간 추출)
```python
if motion_detected:
    out.write(frame2)  # cv2.VideoWriter를 사용해 저장
```


추가 옵션
감지 민감도 조절 (픽셀 변화량, 노이즈 필터링)

연속 움직임만 저장 (1~2초 이상 지속될 때만 저장)

저장할 때 타임스탬프 표시