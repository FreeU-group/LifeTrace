import json
import os

log_file = 'data/logs/core/token_usage_2025-10.jsonl'
print('=== Token使用量日志文件验证 ===')
print(f'文件路径: {log_file}')
print(f'文件大小: {os.path.getsize(log_file)} bytes')

with open(log_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(f'总记录数: {len(lines)}')

    print('\n=== 最新记录格式验证 ===')
    data = json.loads(lines[-1].strip())
    print(f'时间戳: {data.get("timestamp")}')
    print(f'模型: {data.get("model")}')
    print(f'输入tokens: {data.get("input_tokens")}')
    print(f'输出tokens: {data.get("output_tokens")}')
    print(f'总tokens: {data.get("total_tokens")}')
    print(f'接口: {data.get("endpoint")}')
    print(f'响应类型: {data.get("response_type")}')
    print(f'查询长度: {data.get("query_length")}')
    if data.get('additional_info'):
        print(f'附加信息: {data.get("additional_info")}')

    print('\n=== 所有接口类型统计 ===')
    endpoints = {}
    for line in lines:
        data = json.loads(line.strip())
        endpoint = data.get('endpoint')
        endpoints[endpoint] = endpoints.get(endpoint, 0) + 1

    for endpoint, count in endpoints.items():
        print(f'{endpoint}: {count} 次调用')
