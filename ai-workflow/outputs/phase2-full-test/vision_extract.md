# Vision Extract Result

- Run ID: phase2-full-test
- Project: /Users/anan/Documents/澳彩
- Images: 1

## Image 1: vision-redbox-test.svg.png

### Parsed JSON

```json
{
  "image_type": "未知",
  "ocr_text": [
    "澳彩 Vision 测试图",
    "请优先识别红框区域，不要把非红框内容当重点。",
    "红框重点：夜隈灯影弄先生",
    "数字线索：12 34 49",
    "非红框辅助：鸡 马 龙",
    "用途：本地图像识别、OCR、红框区域测试"
  ],
  "marked_regions": [
    {
      "region": "红框",
      "visual_marker": "红色边框",
      "text": [
        "红框重点：夜隈灯影弄先生",
        "数字线索：12 34 49"
      ],
      "objects": [],
      "notes": ""
    }
  ],
  "visual_scene": [],
  "numbers": [
    12,
    34,
    49
  ],
  "possible_clues": [
    "鸡 马 龙"
  ],
  "uncertain": []
}
```

### Raw Response

```json
{
  "image_type": "未知",
  "ocr_text": [
    "澳彩 Vision 测试图",
    "请优先识别红框区域，不要把非红框内容当重点。",
    "红框重点：夜隈灯影弄先生",
    "数字线索：12 34 49",
    "非红框辅助：鸡 马 龙",
    "用途：本地图像识别、OCR、红框区域测试"
  ],
  "marked_regions": [
    {
      "region": "红框",
      "visual_marker": "红色边框",
      "text": ["红框重点：夜隈灯影弄先生", "数字线索：12 34 49"],
      "objects": [],
      "notes": ""
    }
  ],
  "visual_scene": [],
  "numbers": [12, 34, 49],
  "possible_clues": ["鸡 马 龙"],
  "uncertain": []
}
```
