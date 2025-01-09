## 使用过程

1. 先截屏选择牌库
2. 然后勾选英雄
3. 点f1开始自动拿牌
4. 点f2暂停自动拿牌

## 打包命令

先运行第一行
```shell
pyinstaller --onefile --icon=avatar.ico main.py --noconsole
```
然后把main.spec里面的`datas=[]`改成`datas=[('image/*', 'image'),('templates.json', '.')]`

然后运行第二行
```shell
pyinstaller main.spec
```