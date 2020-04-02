import time
import requests


client_params = {
    "url": "http://127.0.0.1:8000/client/",
    "number": [-1, 0, 1, 10, None, "", "1", "a"],
    "grade": [-100, 0, 1, 1000, None, "", "1", "a"],
}

rank_params = {
    "url": "http://127.0.0.1:8000/rank/",
    "number": [-1, 0, 1, 10, None, "", "1", "a"],
    "start": [-1, 0, 1, 10, None, "", "1", "20", "a"],
    "stop": [-1, 0, 5, 10, 20, None, "", "1", "a"],
}


def test_api(file, url, params, body, count, method=None):
    s_time = time.time()
    if method is None or method == "GET":
        resp = requests.get(url, params=params, data=body)
    else:
        resp = requests.post(url, params=params, data=body)
    e_time = time.time()
    file.write("测试{0}：url={1}\n参数: {2}, body: {3}\n".format(count, url, params, body))
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    es = (e_time - s_time) * 1000
    file.write("测试{0}结果: status={1}, response={2}  响应时间：{3}ms\n".format(count, resp.status_code, data, es))


def test_client(file):
    url = client_params.get("url")
    number = client_params.get("number")
    grade = client_params.get("grade")
    file.write("\n==================上传客户端分数接口测试=========================\n")
    count = 1
    for param1 in number:
        for param2 in grade:
            params = {
                "number": param1,
                "grade": param2,
            }
            test_api(file, url, params, body=None, count=count, method="POST")
            count += 1


def test_rank(file):
    url = rank_params.get("url")
    number = rank_params.get("number")
    start = rank_params.get("start")
    stop = rank_params.get("stop")
    file.write("\n==================排行榜接口测试=========================\n")
    count = 1
    for param1 in number:
        for param2 in start:
            for param3 in stop:
                params = {
                    "number": param1,
                    "start": param2,
                    "stop": param3
                }
                test_api(file, url, params, body=None, count=count)
                count += 1


def main():
    with open("test_result.txt", "w", encoding="utf-8") as file:
        test_client(file)
        test_rank(file)


if __name__ == '__main__':
    main()
