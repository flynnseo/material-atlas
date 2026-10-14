---
id: MTL-LT-PIXLED
name_ko: 주소지정 픽셀 LED (WS2812 계열)
name_en: Addressable pixel LED (WS2812)
aliases: [WS2812, WS2812B, 네오픽셀, NeoPixel, 픽셀 LED, 어드레서블 LED, SK6812, APA102, WS2811, 픽셀 스트립, 주소지정 LED, 디지털 LED 스트립, 매직 LED, 드림컬러, DMX 픽셀, SPI LED, WLED, FastLED]
family: light
subfamily: led
form: [profile, sheet]
properties:
  예시 칩: "WS2812B (5 V, RGB, 개별 제어)"
  컨트롤: "DMX / ESP32·Arduino + WLED·FastLED"
look: [glossy]
processes: [bonding]
uses: [lighting, signage, kinetic, installation]
finishes: []
cases: []
novelty: standard
kinetic_fit: "개별 제어 가능한 조명이라 키네틱 연출에 직접 활용."
confidence: C
status: draft
hands_on: false
sources:
  - https://en.wikipedia.org/wiki/LED_strip_light
updated: 2026-10-14
---
## 한 줄 정의
각 LED 에 제어칩이 들어 있어 개별 색·밝기를 제어하는 스트립/모듈로, 미디어 파사드와 키네틱 조명에 쓴다.

## 특성
- WS2812B 는 5 V RGB 개별 제어 칩 (Wikipedia)
- DMX 컨트롤러 또는 ESP32 등 + WLED/FastLED 로 제어 (Wikipedia)
- LED 마다 칩이 있어 체이싱·스트로브 연출 가능 (Wikipedia)
- 긴 런 전압강하 주의 (Wikipedia)

## 가공·마감 메모
- 전원 중간 주입
- 데이터 신호 레벨 시프트(추정)

## 공간/오브제 사용 사례
- 키네틱 조명 연출
- 미디어 파사드
- VMD 애니메이션

## 주의점
- 전압강하
- 전류 과다
- 프로토콜별 호환 주의

## 업체·단가 메모
-

## 직접 해본 것
-
