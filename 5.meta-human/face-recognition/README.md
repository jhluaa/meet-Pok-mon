#  Face Verification Using DeepFace

This project implements various face verification pipelines using DeepFace on CPU. Below is a summary of the available configurations and optimization options.


___  
## Detector Backend Configuration

| **Detector Backend**          | **Detection Accuracy** | **Execution Speed (CPU)** | **Requires Alignment** | **Threshold** | **Remarks**                                                                 |
|-------------------------------|------------------------|---------------------------|------------------------|--------------|-----------------------------------------------------------------------------|
| **Facenet + OpenCV**          | Low                   | Fast (<1 second)          | Yes                    | 0.4          | Suitable for basic applications, but OpenCV has lower detection accuracy.   |
| **VGG-face + SSD**            | Medium                | Fast (<1 second)          | Yes                    | 0.6          | SSD offers higher accuracy than OpenCV while maintaining speed.             |
| **ArcFace + SSD**             | Medium                | Lightweight (~1 second)   | Yes                    | 0.6          | Balances speed, accuracy, and resource usage.                               |
| **Facenet + MTCNN**           | High                  | Moderate (~1-2 seconds)   | Yes                    | 0.3-0.4      | MTCNN provides good detection results and is suitable for high-accuracy tasks. |
| **Facenet512 + RetinaFace**   | Highest               | Slow (~5 seconds)         | No                     | 0.3-0.4      | RetinaFace achieves the best detection accuracy but is slower to execute.   |

---

## Face Alignment Strategy

If the detector backend is not **RetinaFace**, the input face images require manual alignment. The alignment process is as follows:

1. **Frontend Button Alignment**:
   - Implement a "Rotate Alignment" button in the frontend to manually adjust the image orientation.

2. **Automatic Alignment in Main Function**:
   - Call the `verify` function in the `main` function.
   - If the `result` outputs a JSON string, alignment is not needed.
   - If the result is incorrect, automatically rotate the image 1-4 times, which takes about 3-4 seconds.

3. **Set `enforce_detection=False`**:
   - Add the parameter `enforce_detection=False` when calling `deepface.verify`.
   - Even if the image is not aligned, the function will return results, but the accuracy may decrease.

---

## Alignment fuzzy strategy
1. in  deepface/modules/detection.py
   - -img = np.array(Image.fromarray(img).rotate(angle))  
   - +img = np.array(Image.fromarray(img).rotate(angle, resample=Image.BICUBIC))

## Example Code
```python
from deepface import DeepFace

# 调用 verify 函数并关闭强制检测
result = DeepFace.verify(
    img1_path="path_to_img1.jpg",
    img2_path="path_to_img2.jpg",
    model_name="Facenet512",
    threshold=0.39,
    normalization="Facenet2018",
    detector_backend="retinaface",
    expand_percentage=10 
)

# 输出比对结果
print(result)
