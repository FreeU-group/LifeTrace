import os
import time
from paddleocr import PaddleOCR

# 初始化PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='ch')

# 设置监控文件夹
screenshot_dir = 'C:/Users/PC/.lifetrace/screenshots'

while True:
    try:
        # 获取文件夹下所有文件
        files = os.listdir(screenshot_dir)

        # 只处理图片文件
        image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if image_files:
            # 找到最新的文件
            latest_file = max(image_files, key=lambda f: os.path.getmtime(os.path.join(screenshot_dir, f)))

            # 检查是否已有对应的txt文件
            txt_file = 'ocr_'+os.path.splitext(latest_file)[0] + '.txt'
            if txt_file not in files:
                # 进行OCR处理
                image_path = os.path.join(screenshot_dir, latest_file)
                if os.path.isfile(image_path):  # 检查文件是否存在
                    # 记录开始时间
                    start_time = time.time()

                    # 使用PaddleOCR进行识别
                    result = ocr.predict(image_path)
                    # print(result)  # 调试用，输出识别结果到控制台，方便检查识别结果是否正确
                    # 计算推理时间
                    elapsed_time = time.time() - start_time

                    # 提取识别结果
                    ocr_text = ""
                    for idx in range(len(result)):
                        res = result[idx]
                        for line in res:
                            ocr_text += line[1][0] + "\n"

                    # 保存结果到txt文件
                    with open(os.path.join(screenshot_dir, txt_file), 'w', encoding='utf-8') as f:
                        f.write(ocr_text)

                    print(f'已生成OCR结果文件: {txt_file}, 推理用时: {elapsed_time:.2f} 秒')
                else:
                    print(f'文件 {image_path} 不存在，跳过处理')

    except Exception as e:
        print(f'读取文件夹 {screenshot_dir} 时出错: {str(e)}')

    # 每隔0.5秒检查一次
    time.sleep(0.5)
