# NET-WEAVER
A hyperledger network constructor.

## 搭建
+ 环境配置: Linux, Docker 和 Docker Compose需要预先安装
+ 工作目录的bin目录下需要包含hyperledger fabric 2.2.2的可执行文件[https://github.com/hyperledger/fabric/releases/tag/v2.2.2](https://github.com/hyperledger/fabric/releases/tag/v2.2.2)
+ 依赖: flask, flask_cors, jinja2

```
pip install -r requirements.txt 
```

## 服务器启动
```
./startapp.sh
```

## 接口

### **/generate [POST]**

+ Content Type: JSON

+ 格式: 
``` JSON
{
    "project": "<project-name>",
    "peers": [
       {
           "index": 1,
           "nodes": 1
       },
       {
           "index": 2,
           "nodes": 1
       },
       {
           "index": 3,
           "nodes": 1
       },
       ...
    ],
    "channels": [
        {
            "peerorgs": [1, 2]
        },
        {
            "peerorgs": [2, 3]
        },
        ...
    ]
}
```
+ 返回内容:
``` JSON
{"status": "OK"}
```

### **/activate [GET]**
Param: project=<projectname>

### **/list     [GET]**

+ 返回内容
``` JSON
{
    "status": "OK', 
    "networks": [networks...],
}
```
### **/get      [GET]**
+ Param: project=<projectname>

### **/suspend  [GET]**
+ Param: project=<projectname>

### **/remove   [GET]**
+ Param: project=<projectname>

### **/newcc    [POST]** (不稳定)

+ Content Type: JSON

+ 格式:
``` JSON
{
"channel": "<channel-name>",
"cc_name": "chaincode-name",
"cc_path_origin": "<chaincode-path-on-server>",
"cc_path": "chaincode-path-will-copy-to",
"cc_lang": "chaincode-language(go/javascript)",
"cc_version": "1.0",
"cc_seq": "1",
"init_func": "chaincode init function"
}
```

## 分类器

+ 文件: network_chebnet.py
+ 依赖: torch, torch_geometric