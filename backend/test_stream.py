import requests

url = "http://localhost:5000/qa/chat"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFiY2QiLCJleHAiOjE3NDc1NDQ5NDF9.QIdrSfd6YykTqbo6-A1poB_sTS9WL2-p6gwcNpqFy08"
}
data = {
    "question": "请你给我一百字的段落，我想测试流式回复",
    "historyId": "123",
    "rag": "true"
}

with requests.post(url, headers=headers, data=data, stream=True) as resp:
    for chunk in resp.iter_content(chunk_size=10, decode_unicode=True):
        if chunk:
            print(chunk, end='', flush=True)
